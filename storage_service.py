import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

def save_local(file_path: str, target_filename: str = None) -> str:
    """Given a downloaded file path (already saved by telegram client) move/rename it into uploads and return relative path."""
    src = Path(file_path)
    if not src.exists():
        raise FileNotFoundError(f"File {file_path} not found")

    if not target_filename:
        target_filename = src.name

    dest = UPLOADS_DIR / target_filename
    # If same path, do nothing
    if src.resolve() != dest.resolve():
        src.rename(dest)
    logger.info(f"Saved file to {dest}")
    return str(dest)

def get_public_url(path: str, base_url: str = None) -> str:
    """Return a public URL for the stored file if base_url provided, otherwise local path."""
    if base_url:
        return f"{base_url.rstrip('/')}/{Path(path).name}"
    return path
