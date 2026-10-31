"""CLI script and programmatic runner for official WCAG source ingestion and vector indexing."""

import argparse
import asyncio
import uuid
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.base import utc_now
from app.db.models.knowledge import KnowledgeChunk, KnowledgeSource
from app.db.session import get_session_maker
from app.rag.chunker import chunk_section
from app.rag.embeddings import get_embedding_service
from app.rag.fetcher import SourceFetcher
from app.rag.parser import parse_source_document
from app.rag.vector_store import get_vector_store

logger = get_logger("knowledge_ingestion")


async def run_ingestion(
    sources_yaml_path: Path,
    dry_run: bool = False,
    source_key_filter: str | None = None,
    reindex: bool = False,
    use_cache: bool = True,
    db: AsyncSession | None = None,
    raw_storage_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute end-to-end ingestion pipeline from sources.yaml into PostgreSQL and Qdrant."""
    if not sources_yaml_path.exists():
        raise FileNotFoundError(f"Sources registry file not found: {sources_yaml_path}")

    with open(sources_yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    source_specs = data.get("sources", [])
    if source_key_filter:
        source_specs = [s for s in source_specs if s.get("source_key") == source_key_filter]

    embedding_service = get_embedding_service()
    vector_store = get_vector_store()

    if reindex and not dry_run:
        vector_store.recreate_collection()

    fetcher = SourceFetcher(raw_storage_dir=raw_storage_dir)

    stats = {
        "sources_processed": 0,
        "total_sections_parsed": 0,
        "total_chunks_created": 0,
        "chunks_persisted": 0,
        "chunks_skipped_unchanged": 0,
        "vectors_upserted": 0,
        "dry_run": dry_run,
    }

    async def _process_with_session(session: AsyncSession) -> None:
        for spec in source_specs:
            if not spec.get("is_active", True):
                continue

            s_key = spec["source_key"]
            s_title = spec["title"]
            s_url = spec["source_url"]
            publisher = spec.get("publisher", "W3C")
            std_ver = spec.get("standard_version", "WCAG 2.2")
            parser_type = spec.get("parser_type", "w3c_tr_single")

            logger.info("Processing knowledge source", source_key=s_key, title=s_title)

            # 1. Fetch document
            try:
                doc = await fetcher.fetch(s_url, source_key=s_key, use_cache=use_cache)
            except Exception as e:
                logger.error(
                    "Failed to fetch knowledge source", source_key=s_key, url=s_url, error=str(e)
                )
                continue

            # 2. Find or create KnowledgeSource record
            source_rec = None
            if not dry_run:
                res = await session.execute(
                    select(KnowledgeSource).where(KnowledgeSource.source_key == s_key)
                )
                source_rec = res.scalar_one_or_none()
                if source_rec is None:
                    source_rec = KnowledgeSource(
                        source_key=s_key,
                        title=s_title,
                        source_url=s_url,
                        publisher=publisher,
                        standard_version=std_ver,
                        fetched_at=utc_now(),
                        checksum=doc.checksum,
                    )
                    session.add(source_rec)
                    await session.flush()
                else:
                    source_rec.fetched_at = utc_now()
                    source_rec.checksum = doc.checksum
                    await session.flush()

            # 3. Parse sections
            sections = parse_source_document(
                html=doc.content,
                base_url=doc.url,
                source_key=s_key,
                parser_type=parser_type,
            )
            stats["total_sections_parsed"] += len(sections)

            # 4. Generate criterion-aware chunks
            source_chunks = []
            for sec in sections:
                chunks = chunk_section(sec, source_metadata=spec)
                source_chunks.extend(chunks)

            stats["total_chunks_created"] += len(source_chunks)

            # 5. Persist chunks idempotently and index in Qdrant
            qdrant_points: list[tuple[uuid.UUID, list[float], dict[str, Any]]] = []

            for chunk_payload in source_chunks:
                if dry_run:
                    continue

                assert source_rec is not None
                # Check for existing chunk with same chunk_key
                c_res = await session.execute(
                    select(KnowledgeChunk).where(
                        KnowledgeChunk.chunk_key == chunk_payload.chunk_key
                    )
                )
                existing_chunk = c_res.scalar_one_or_none()

                if existing_chunk is not None:
                    if existing_chunk.content_hash == chunk_payload.content_hash and not reindex:
                        # Unchanged: skip re-embedding
                        stats["chunks_skipped_unchanged"] += 1
                        continue

                    # Content changed: update
                    existing_chunk.content = chunk_payload.content
                    existing_chunk.content_hash = chunk_payload.content_hash
                    existing_chunk.chunk_metadata = chunk_payload.metadata
                    existing_chunk.section_title = chunk_payload.section_title
                    existing_chunk.criterion_id = chunk_payload.criterion_id
                    existing_chunk.criterion_level = chunk_payload.criterion_level
                    existing_chunk.principle = chunk_payload.principle
                    existing_chunk.indexed_at = utc_now()
                    target_chunk_id = existing_chunk.id
                    stats["chunks_persisted"] += 1
                else:
                    new_chunk = KnowledgeChunk(
                        source_id=source_rec.id,
                        chunk_key=chunk_payload.chunk_key,
                        criterion_id=chunk_payload.criterion_id,
                        criterion_level=chunk_payload.criterion_level,
                        principle=chunk_payload.principle,
                        section_title=chunk_payload.section_title,
                        content_type=chunk_payload.content_type,
                        content=chunk_payload.content,
                        source_url=chunk_payload.source_url,
                        chunk_metadata=chunk_payload.metadata,
                        content_hash=chunk_payload.content_hash,
                        embedding_model=embedding_service.model_name,
                        indexed_at=utc_now(),
                    )
                    session.add(new_chunk)
                    await session.flush()
                    target_chunk_id = new_chunk.id
                    stats["chunks_persisted"] += 1

                # Generate vector embedding
                vector = embedding_service.embed_query(chunk_payload.content)
                payload = {
                    "chunk_id": str(target_chunk_id),
                    "chunk_key": chunk_payload.chunk_key,
                    "source_key": s_key,
                    "criterion_id": chunk_payload.criterion_id,
                    "criterion_level": chunk_payload.criterion_level,
                    "content_type": chunk_payload.content_type,
                    "section_title": chunk_payload.section_title,
                    "source_url": chunk_payload.source_url,
                    "content_hash": chunk_payload.content_hash,
                    "content": chunk_payload.content[:500],  # preview for inspection
                }
                qdrant_points.append((target_chunk_id, vector, payload))

            if qdrant_points and not dry_run:
                vector_store.upsert_chunks(qdrant_points)
                stats["vectors_upserted"] += len(qdrant_points)

            if not dry_run:
                await session.commit()
            stats["sources_processed"] += 1

    if db is not None:
        await _process_with_session(db)
    else:
        session_maker = get_session_maker()
        async with session_maker() as session:
            await _process_with_session(session)

    return stats


def main() -> None:
    """CLI entrypoint for knowledge ingestion."""
    parser = argparse.ArgumentParser(description="AccessGuard AI WCAG Knowledge Ingestion")
    parser.add_argument(
        "--sources",
        type=Path,
        default=Path(__file__).parent.parent.parent / "knowledge_base" / "sources.yaml",
        help="Path to sources.yaml registry",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate documents without persisting to DB or vector store",
    )
    parser.add_argument(
        "--source-key",
        type=str,
        default=None,
        help="Filter ingestion to a single source_key",
    )
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Recreate Qdrant collection and recompute all vector embeddings",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass local raw document cache and re-fetch from official URLs",
    )

    args = parser.parse_args()

    raw_dir = Path(__file__).parent.parent.parent / "knowledge_base" / "raw"
    results = asyncio.run(
        run_ingestion(
            sources_yaml_path=args.sources,
            dry_run=args.dry_run,
            source_key_filter=args.source_key,
            reindex=args.reindex,
            use_cache=not args.no_cache,
            raw_storage_dir=raw_dir,
        )
    )

    print("\n--- AccessGuard AI Knowledge Ingestion Summary ---")
    for k, v in results.items():
        print(f"  {k:28}: {v}")
    print("---------------------------------------------------\n")


if __name__ == "__main__":
    main()
