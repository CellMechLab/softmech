"""
Pipeline system - descriptor and executor.
"""

from .descriptor import (
    PipelineDescriptor,
    PipelineStep,
    PipelineStage,
    PipelineMetadata,
    ProcessingStepType,
)
from .executor import PipelineExecutor, ExecutionContext

__all__ = [
    "PipelineDescriptor",
    "PipelineStep",
    "PipelineStage",
    "PipelineMetadata",
    "ProcessingStepType",
    "PipelineExecutor",
    "ExecutionContext",
]
