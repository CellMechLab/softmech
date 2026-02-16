"""
Pipeline descriptor - defines processing workflows as serializable structures.

A PipelineDescriptor can be saved to JSON/YAML and reused across different datasets.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
from enum import Enum


class ProcessingStepType(Enum):
    """Types of processing steps in a pipeline."""

    FILTER = "filter"
    CONTACT_POINT = "contact_point"
    INDENTATION = "indentation"
    ELASTICITY_SPECTRA = "elasticity_spectra"
    FORCE_MODEL = "force_model"
    ELASTIC_MODEL = "elastic_model"
    EXPORTER = "exporter"


@dataclass
class PipelineStep:
    """Single step in a pipeline."""

    type: str  # Processing step type
    plugin_id: str  # Which plugin to use
    parameters: Dict[str, Any] = field(default_factory=dict)
    plugin_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "PipelineStep":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class PipelineStage:
    """
    A logical stage in the pipeline (preprocessing or analysis).

    This allows splitting pipelines into two parts:
    - Preprocessing: filtering, contact point, indentation
    - Analysis: elasticity spectra, model fitting
    """

    name: str  # e.g., 'preprocessing', 'analysis'
    description: str = ""
    steps: List[PipelineStep] = field(default_factory=list)

    def add_step(self, step: PipelineStep) -> None:
        """Add a processing step."""
        self.steps.append(step)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PipelineStage":
        """Create from dictionary."""
        steps = [PipelineStep.from_dict(s) for s in data.get("steps", [])]
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            steps=steps,
        )


@dataclass
class PipelineMetadata:
    """Metadata about a pipeline."""

    name: str
    description: str = ""
    version: str = "1.0"  # Pipeline version (different from plugin versions)
    author: str = ""
    created: datetime = field(default_factory=datetime.now)
    modified: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "created": self.created.isoformat(),
            "modified": self.modified.isoformat(),
            "tags": self.tags,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PipelineMetadata":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            author=data.get("author", ""),
            created=datetime.fromisoformat(data.get("created", datetime.now().isoformat())),
            modified=datetime.fromisoformat(data.get("modified", datetime.now().isoformat())),
            tags=data.get("tags", []),
            notes=data.get("notes", ""),
        )


class PipelineDescriptor:
    """
    Describes a complete AFM analysis pipeline.

    Can be serialized to JSON and reused across datasets.
    Supports two-stage pipelines (preprocessing + analysis).
    """

    def __init__(
        self,
        metadata: PipelineMetadata,
        stages: Optional[List[PipelineStage]] = None,
        steps: Optional[List[PipelineStep]] = None,
    ):
        """
        Initialize a PipelineDescriptor.

        Can define either as stages (recommended) or flat list of steps.

        Parameters
        ----------
        metadata : PipelineMetadata
            Pipeline metadata
        stages : list of PipelineStage, optional
            Organized pipeline stages
        steps : list of PipelineStep, optional
            Flat list of steps (if not using stages)
        """
        self.metadata = metadata
        self.stages = stages or []
        self.steps = steps or []

    def add_stage(self, stage: PipelineStage) -> None:
        """Add a processing stage."""
        self.stages.append(stage)

    def add_step(self, step: PipelineStep) -> None:
        """Add a step to flat workflow (if not using stages)."""
        self.steps.append(step)

    def get_all_steps(self) -> List[PipelineStep]:
        """
        Get all steps in order (from all stages or flat list).

        Returns
        -------
        list
            All ProcessingStep objects in execution order
        """
        if self.stages:
            steps = []
            for stage in self.stages:
                steps.extend(stage.steps)
            return steps
        return self.steps

    def get_stage(self, name: str) -> Optional[PipelineStage]:
        """Get a stage by name."""
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns
        -------
        dict
            Serializable dictionary representation
        """
        result = {
            "version": "2.0",  # SoftMech pipeline format version
            "metadata": self.metadata.to_dict(),
        }

        if self.stages:
            result["stages"] = [stage.to_dict() for stage in self.stages]
        else:
            result["steps"] = [step.to_dict() for step in self.steps]

        return result

    def to_json(self) -> str:
        """
        Serialize to JSON string.

        Returns
        -------
        str
            JSON representation
        """
        data = self.to_dict()
        # Custom JSON encoder for datetime objects
        return json.dumps(data, indent=2, default=str)

    def save(self, filename: str) -> None:
        """
        Save pipeline to JSON file.

        Parameters
        ----------
        filename : str
            Output file path
        """
        with open(filename, "w") as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: Dict) -> "PipelineDescriptor":
        """
        Create from dictionary.

        Parameters
        ----------
        data : dict
            Dictionary from to_dict() or loaded JSON

        Returns
        -------
        PipelineDescriptor
            Reconstructed pipeline
        """
        metadata = PipelineMetadata.from_dict(data["metadata"])

        # Handle both staged and flat workflows
        stages = []
        if "stages" in data:
            stages = [PipelineStage.from_dict(s) for s in data["stages"]]

        steps = []
        if "steps" in data:
            steps = [PipelineStep.from_dict(s) for s in data["steps"]]

        return cls(metadata=metadata, stages=stages, steps=steps)

    @classmethod
    def from_json(cls, json_str: str) -> "PipelineDescriptor":
        """
        Deserialize from JSON string.

        Parameters
        ----------
        json_str : str
            JSON string

        Returns
        -------
        PipelineDescriptor
            Reconstructed pipeline
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def load(cls, filename: str) -> "PipelineDescriptor":
        """
        Load pipeline from JSON file.

        Parameters
        ----------
        filename : str
            Input file path

        Returns
        -------
        PipelineDescriptor
            Loaded pipeline
        """
        with open(filename, "r") as f:
            return cls.from_json(f.read())
