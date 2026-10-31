"""Criterion-aware text chunker and metadata generator for WCAG knowledge base."""

import hashlib
import re
from typing import Any

from app.rag.parser import ParsedSection

DEFAULT_CHUNK_SIZE = 1500  # ~350-400 words
DEFAULT_CHUNK_OVERLAP = 200


class ChunkPayload:
    """Prepared knowledge chunk with canonical metadata and deterministic hash."""

    def __init__(
        self,
        chunk_key: str,
        content: str,
        source_url: str,
        content_type: str,
        content_hash: str,
        criterion_id: str | None = None,
        criterion_level: str | None = None,
        principle: str | None = None,
        guideline_id: str | None = None,
        section_title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.chunk_key = chunk_key
        self.content = content
        self.source_url = source_url
        self.content_type = content_type
        self.content_hash = content_hash
        self.criterion_id = criterion_id
        self.criterion_level = criterion_level
        self.principle = principle
        self.guideline_id = guideline_id
        self.section_title = section_title
        self.metadata = metadata or {}


def compute_content_hash(text: str) -> str:
    """Compute SHA-256 hash of normalized text."""
    normalized = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def chunk_section(
    section: ParsedSection,
    source_metadata: dict[str, Any],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    _chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[ChunkPayload]:
    """Chunk a parsed section while preserving criterion identification and semantic integrity."""
    chunks: list[ChunkPayload] = []
    text = section.content.strip()

    source_key = source_metadata.get("source_key", "wcag")
    publisher = source_metadata.get("publisher", "W3C")
    standard_version = source_metadata.get("standard_version", "WCAG 2.2")
    source_title = source_metadata.get("title", "Accessibility Guidelines")

    # If the section text fits comfortably within chunk size, keep it intact as a single unit
    if len(text) <= chunk_size:
        c_hash = compute_content_hash(text)
        chunk_key = (
            f"{section.section_key}_normative"
            if section.criterion_id
            else f"{section.section_key}_full"
        )
        meta = {
            "chunk_id": chunk_key,
            "source_key": source_key,
            "source_title": source_title,
            "source_url": section.source_url,
            "publisher": publisher,
            "standard_version": standard_version,
            "criterion_id": section.criterion_id,
            "criterion_level": section.criterion_level,
            "principle": section.principle,
            "guideline_id": section.guideline_id,
            "content_type": section.content_type,
            "section_title": section.section_title,
            "content_hash": c_hash,
            **section.metadata,
        }
        chunks.append(
            ChunkPayload(
                chunk_key=chunk_key,
                content=text,
                source_url=section.source_url,
                content_type=section.content_type,
                content_hash=c_hash,
                criterion_id=section.criterion_id,
                criterion_level=section.criterion_level,
                principle=section.principle,
                guideline_id=section.guideline_id,
                section_title=section.section_title,
                metadata=meta,
            )
        )
        return chunks

    # If text exceeds chunk size, split by paragraphs while repeating criterion header context
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    current_chunk_parts: list[str] = []
    current_length = 0
    sub_index = 1

    header_context = f"{section.section_title}." if section.section_title else ""

    for paragraph in paragraphs:
        p_len = len(paragraph)
        if current_length + p_len > chunk_size and current_chunk_parts:
            # Emit current chunk
            body = " ".join(current_chunk_parts)
            full_text = f"{header_context} {body}".strip() if header_context else body
            c_hash = compute_content_hash(full_text)
            c_key = f"{section.section_key}_p{sub_index}"
            meta = {
                "chunk_id": c_key,
                "source_key": source_key,
                "source_title": source_title,
                "source_url": section.source_url,
                "publisher": publisher,
                "standard_version": standard_version,
                "criterion_id": section.criterion_id,
                "criterion_level": section.criterion_level,
                "principle": section.principle,
                "guideline_id": section.guideline_id,
                "content_type": section.content_type,
                "section_title": section.section_title,
                "content_hash": c_hash,
                "part_index": sub_index,
                **section.metadata,
            }
            chunks.append(
                ChunkPayload(
                    chunk_key=c_key,
                    content=full_text,
                    source_url=section.source_url,
                    content_type=section.content_type,
                    content_hash=c_hash,
                    criterion_id=section.criterion_id,
                    criterion_level=section.criterion_level,
                    principle=section.principle,
                    guideline_id=section.guideline_id,
                    section_title=section.section_title,
                    metadata=meta,
                )
            )
            sub_index += 1
            current_chunk_parts = [paragraph]
            current_length = p_len
        else:
            current_chunk_parts.append(paragraph)
            current_length += p_len

    if current_chunk_parts:
        body = " ".join(current_chunk_parts)
        full_text = f"{header_context} {body}".strip() if header_context else body
        c_hash = compute_content_hash(full_text)
        c_key = f"{section.section_key}_p{sub_index}"
        meta = {
            "chunk_id": c_key,
            "source_key": source_key,
            "source_title": source_title,
            "source_url": section.source_url,
            "publisher": publisher,
            "standard_version": standard_version,
            "criterion_id": section.criterion_id,
            "criterion_level": section.criterion_level,
            "principle": section.principle,
            "guideline_id": section.guideline_id,
            "content_type": section.content_type,
            "section_title": section.section_title,
            "content_hash": c_hash,
            "part_index": sub_index,
            **section.metadata,
        }
        chunks.append(
            ChunkPayload(
                chunk_key=c_key,
                content=full_text,
                source_url=section.source_url,
                content_type=section.content_type,
                content_hash=c_hash,
                criterion_id=section.criterion_id,
                criterion_level=section.criterion_level,
                principle=section.principle,
                guideline_id=section.guideline_id,
                section_title=section.section_title,
                metadata=meta,
            )
        )

    return chunks
