"""Shared helpers for diagnostic PNG generation."""

import shutil
from contextlib import contextmanager
from pathlib import Path

from app.database import SessionLocal


OUTPUT_DIR = Path("output") / "plots"
DRILLDOWN_OUTPUT_DIR = OUTPUT_DIR / "drilldown_outputs"


def ensure_output_dir() -> Path:
    """Create and return the directory used for generated PNG diagnostics."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def ensure_drilldown_output_dir() -> Path:
    """Create and return the directory used for drilldown outputs."""
    DRILLDOWN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return DRILLDOWN_OUTPUT_DIR


def clear_drilldown_output_dir() -> None:
    """Clear all files inside drilldown_outputs folder."""
    if DRILLDOWN_OUTPUT_DIR.exists():
        for child in DRILLDOWN_OUTPUT_DIR.iterdir():
            if child.is_file() or child.is_symlink():
                child.unlink()
            elif child.is_dir():
                shutil.rmtree(child)
    else:
        DRILLDOWN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def database_session(existing_session=None):
    """Use the supplied session or close a temporary visualization session."""
    if existing_session is not None:
        yield existing_session
        return
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
