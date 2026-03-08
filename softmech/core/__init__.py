"""
Core SoftMech functionality - algorithms, data structures, and pipelines.

No UI dependencies here - pure Python for maximum reusability.
"""

from . import plugins
from . import data
from . import algorithms
from . import io
from . import pipeline

__all__ = ["plugins", "data", "algorithms", "io", "pipeline"]
