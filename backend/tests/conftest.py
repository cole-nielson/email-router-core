"""
Backend test conftest.py that imports all fixtures from the fixtures directory.

This maintains backward compatibility while organizing fixtures properly.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


# Import all fixtures from the centralized fixtures directory
# This makes all fixtures available to tests throughout the test suite
from .fixtures.conftest import *  # noqa: F401, F403
