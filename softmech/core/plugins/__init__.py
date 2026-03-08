"""
Plugin system for SoftMech.

Provides base classes and registry for extensible plugin architecture.
Plugins can be contributed by users - just add a .py file to the plugins directory.
"""

from .base import (
    PluginBase,
    Filter,
    ContactPointDetector,
    ForceModel,
    ElasticModel,
    Exporter,
)
from .registry import PluginRegistry

__all__ = [
    "PluginBase",
    "Filter",
    "ContactPointDetector",
    "ForceModel",
    "ElasticModel",
    "Exporter",
    "PluginRegistry",
]
