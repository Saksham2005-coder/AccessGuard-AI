"""Tenant-safe artifact storage service for screenshots, snapshots, and reports."""

import os
import uuid
from pathlib import Path

from app.config import get_settings


def get_storage_root() -> Path:
    """Resolve and ensure the artifact storage root directory."""
    settings = get_settings()
    configured_path = Path(settings.ARTIFACT_STORAGE_DIR)

    # In local development or Windows test environments where /app/storage does not exist
    if not configured_path.is_absolute() or os.name == "nt" or not configured_path.exists():
        # Fallback to local backend/data/storage
        local_backend_dir = Path(__file__).resolve().parent.parent.parent
        storage_dir = local_backend_dir / "data" / "storage"
    else:
        storage_dir = configured_path

    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


def save_page_screenshot(
    scan_id: uuid.UUID,
    page_id: uuid.UUID,
    image_bytes: bytes,
) -> str:
    """Save page screenshot to storage root and return relative storage key."""
    storage_root = get_storage_root()
    screenshot_dir = storage_root / "screenshots" / str(scan_id)
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{page_id}.png"
    file_path = screenshot_dir / filename
    file_path.write_bytes(image_bytes)

    # Return normalized relative storage key
    return f"screenshots/{scan_id}/{filename}"


def resolve_artifact_path(storage_key: str) -> Path | None:
    """Safely resolve an artifact storage key preventing path traversal."""
    if not storage_key or ".." in storage_key or storage_key.startswith(("/", "\\")):
        return None

    storage_root = get_storage_root().resolve()
    target_path = (storage_root / storage_key).resolve()

    # Prevent directory traversal outside storage root
    if not str(target_path).startswith(str(storage_root)):
        return None

    if not target_path.is_file():
        return None

    return target_path
