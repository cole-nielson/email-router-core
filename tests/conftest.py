"""
Root conftest.py that imports all fixtures from the fixtures directory.

This maintains backward compatibility while organizing fixtures properly.
"""

# Import all fixtures from the centralized fixtures directory
# This makes all fixtures available to tests throughout the test suite
from .fixtures.conftest import *  # noqa: F401, F403
