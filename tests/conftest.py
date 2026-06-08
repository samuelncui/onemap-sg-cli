"""Shared test fixtures and helpers."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def has_credentials() -> bool:
    """Check if OneMap credentials are available."""
    return bool(os.getenv("ONEMAP_EMAIL") and os.getenv("ONEMAP_EMAIL_PASSWORD"))


def onemap_cli(*args: str) -> subprocess.CompletedProcess:
    """Run `onemap` CLI and return CompletedProcess."""
    return subprocess.run(
        [sys.executable, "-m", "onemap_sg.cli", *args],
        capture_output=True, text=True, timeout=30,
        cwd=str(PROJECT_ROOT),
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
    )


# Skip decorators
requires_credentials = pytest.mark.skipif(
    not has_credentials(), reason="ONEMAP_EMAIL / ONEMAP_EMAIL_PASSWORD not set"
)
