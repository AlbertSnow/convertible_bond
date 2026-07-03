"""Ensure project root is on sys.path for scripts run from any cwd."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def setup_project_path():
    root = str(PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    return PROJECT_ROOT
