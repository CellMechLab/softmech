"""
Core data structures for SoftMech.

Defines Curve and Dataset classes that hold AFM measurements and results.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime


@dataclass
class TipGeometry:
    """Describes AFM tip geometry."""

    geometry_type: str  # 'sphere', 'cone', 'pyramid', 'cylinder'
    radius: Optional[float] = None  # For sphere and cylinder (m)
    angle: Optional[float] = None  # For cone and pyramid (degrees)
    value: Optional[float] = None  # Backward compatibility

    def validate(self) -> bool:
        """Check if geometry is valid."""
        valid_types = {"sphere", "cone", "pyramid", "cylinder"}
        if self.geometry_type not in valid_types:
            return False
        if self.geometry_type in ("sphere", "cylinder") and self.radius is None:
            return False
        if self.geometry_type in ("cone", "pyramid") and self.angle is None:
            return False
        return True


@dataclass
class CurveRawData:
    """Raw force-displacement measurement."""

    Z: np.ndarray  # Displacement (m)
    F: np.ndarray  # Force (N)

    def __post_init__(self):
        """Ensure arrays are numpy arrays."""
        self.Z = np.asarray(self.Z)
        self.F = np.asarray(self.F)

        if len(self.Z) != len(self.F):
            raise ValueError("Z and F must have same length")


@dataclass
class ProcessingResult:
    """Results from a single processing step."""

    step_name: str  # e.g., 'filtering', 'contact_point', 'indentation'
    plugin_id: str  # e.g., 'savgol'
    plugin_version: str  # e.g., '1.0.0'
    parameters: Dict[str, Any]  # Parameters used
    timestamp: datetime = field(default_factory=datetime.now)

    # For spectral analysis steps
    Z: Optional[np.ndarray] = None
    F: Optional[np.ndarray] = None

    # For contact point detection
    contact_point: Optional[Tuple[float, float]] = None  # (Z_cp, F_cp)

    # For function extraction steps
    indentation: Optional[np.ndarray] = None  # δ values
    force_from_indentation: Optional[np.ndarray] = None  # F values for indentation

    elasticity_depth: Optional[np.ndarray] = None  # δ_e values
    elasticity: Optional[np.ndarray] = None  # E values

    # For model fitting
    fitted_parameters: Optional[Dict[str, Any]] = None


class Curve:
    """
    Represents a single AFM force-displacement measurement.

    Similar to the previous engine.curve but cleaner and more modular.
    """

    def __init__(
        self,
        Z: np.ndarray,
        F: np.ndarray,
        spring_constant: float = 1.0,
        tip_geometry: Optional[TipGeometry] = None,
        index: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a Curve.

        Parameters
        ----------
        Z : np.ndarray
            Displacement values (m)
        F : np.ndarray
            Force values (N)
        spring_constant : float
            Cantilever spring constant (N/m)
        tip_geometry : TipGeometry, optional
            AFM tip geometry description
        index : int, optional
            Index in dataset (for identification)
        metadata : dict, optional
            Additional metadata
        """
        self.raw_data = CurveRawData(Z=Z, F=F)
        self.spring_constant = spring_constant
        self.tip_geometry = tip_geometry or TipGeometry(geometry_type="sphere", radius=1e-6)
        self.index = index
        self.metadata = metadata or {}

        # Outlier flag
        self.is_outlier = False

        # Processing history (list of ProcessingResult objects)
        self.processing_history: List[ProcessingResult] = []

        # Current state after last successful processing step
        self._Z: Optional[np.ndarray] = None  # Current Z data (potentially filtered)
        self._F: Optional[np.ndarray] = None  # Current F data (potentially filtered)
        self._contact_point: Optional[Tuple[float, float]] = None

        # Derived quantities
        self._indentation: Optional[np.ndarray] = None  # δ = Z - F/k
        self._force_indentation: Optional[np.ndarray] = None  # F at indentation

        self._elasticity_depth: Optional[np.ndarray] = None  # δ for elasticity spectra
        self._elasticity: Optional[np.ndarray] = None  # E values

        # Fitted parameters
        self._force_model_params: Optional[Any] = None
        self._elastic_model_params: Optional[Any] = None

    def reset_to_raw(self) -> None:
        """Reset to raw data state, clearing all processing."""
        self._Z = self.raw_data.Z.copy()
        self._F = self.raw_data.F.copy()
        self._contact_point = None
        self._indentation = None
        self._force_indentation = None
        self._elasticity_depth = None
        self._elasticity = None
        self._force_model_params = None
        self._elastic_model_params = None
        self.processing_history = []

    def set_filtered_data(self, Z: np.ndarray, F: np.ndarray) -> None:
        """
        Set filtered curve data (from filter plugin).

        Parameters
        ----------
        Z : np.ndarray
            Filtered displacement
        F : np.ndarray
            Filtered force
        """
        self._Z = np.asarray(Z)
        self._F = np.asarray(F)

    def get_current_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get current (potentially filtered) curve data.

        Returns
        -------
        tuple
            (Z, F) arrays
        """
        if self._Z is None:
            self.reset_to_raw()
        return self._Z.copy(), self._F.copy()

    def set_contact_point(self, Z_contact: float, F_contact: float) -> None:
        """
        Set the detected contact point.

        Parameters
        ----------
        Z_contact : float
            Z displacement at contact
        F_contact : float
            Force at contact
        """
        self._contact_point = (Z_contact, F_contact)

    def get_contact_point(self) -> Optional[Tuple[float, float]]:
        """Get the detected contact point."""
        return self._contact_point

    def set_indentation_data(self, indentation: np.ndarray, force: np.ndarray) -> None:
        """
        Set indentation data (δ, F).

        Parameters
        ----------
        indentation : np.ndarray
            Indentation depth values (m)
        force : np.ndarray
            Force values (N)
        """
        self._indentation = np.asarray(indentation)
        self._force_indentation = np.asarray(force)

    def get_indentation_data(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Get indentation data.

        Returns
        -------
        tuple
            (indentation, force) or (None, None) if not available
        """
        return self._indentation, self._force_indentation

    def set_elasticity_spectra(self, depth: np.ndarray, modulus: np.ndarray) -> None:
        """
        Set elasticity spectra data E(δ).

        Parameters
        ----------
        depth : np.ndarray
            Indentation depth values (m)
        modulus : np.ndarray
            Young's modulus values (Pa)
        """
        self._elasticity_depth = np.asarray(depth)
        self._elasticity = np.asarray(modulus)

    def get_elasticity_spectra(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Get elasticity spectra.

        Returns
        -------
        tuple
            (depth, modulus) or (None, None) if not available
        """
        return self._elasticity_depth, self._elasticity

    def set_force_model_params(self, params: Any) -> None:
        """Set fitted force model parameters."""
        self._force_model_params = params

    def get_force_model_params(self) -> Optional[Any]:
        """Get fitted force model parameters."""
        return self._force_model_params

    def set_elastic_model_params(self, params: Any) -> None:
        """Set fitted elastic model parameters."""
        self._elastic_model_params = params

    def get_elastic_model_params(self) -> Optional[Any]:
        """Get fitted elastic model parameters."""
        return self._elastic_model_params

    def toggle_outlier(self) -> bool:
        """
        Toggle outlier status.

        Returns
        -------
        bool
            New outlier status
        """
        self.is_outlier = not self.is_outlier
        return self.is_outlier

    def set_outlier(self, is_outlier: bool) -> None:
        """
        Set outlier status.

        Parameters
        ----------
        is_outlier : bool
            Whether this curve is an outlier
        """
        self.is_outlier = is_outlier

    def record_processing_step(self, result: ProcessingResult) -> None:
        """
        Record a processing step in the history.

        Parameters
        ----------
        result : ProcessingResult
            Information about the step
        """
        self.processing_history.append(result)

    def get_processing_history(self) -> List[ProcessingResult]:
        """Get the processing history."""
        return self.processing_history.copy()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert curve to dictionary (for serialization).

        Returns
        -------
        dict
            Dictionary representation
        """
        return {
            "Z": self.raw_data.Z,
            "F": self.raw_data.F,
            "spring_constant": self.spring_constant,
            "tip_geometry": {
                "type": self.tip_geometry.geometry_type,
                "radius": self.tip_geometry.radius,
                "angle": self.tip_geometry.angle,
            },
            "index": self.index,
            "metadata": self.metadata,
            "is_outlier": self.is_outlier,
        }


@dataclass
class Dataset:
    """Collection of Curve measurements."""

    curves: List[Curve] = field(default_factory=list)
    name: str = "Unnamed Dataset"
    created: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        """Number of curves in dataset."""
        return len(self.curves)

    def __getitem__(self, index: int) -> Curve:
        """Get curve by index."""
        return self.curves[index]

    def __iter__(self):
        """Iterate over curves."""
        return iter(self.curves)

    def append(self, curve: Curve) -> None:
        """Add a curve to the dataset."""
        curve.index = len(self.curves)
        self.curves.append(curve)

    def remove(self, index: int) -> None:
        """Remove a curve by index."""
        self.curves.pop(index)
        # Re-index remaining curves
        for i, curve in enumerate(self.curves):
            curve.index = i

    def get_force_parameters(self) -> Optional[np.ndarray]:
        """
        Extract force model parameters from all curves.

        Returns
        -------
        np.ndarray or None
            Array of shape (n_curves, n_params) if all curves have parameters
        """
        params = []
        for curve in self.curves:
            p = curve.get_force_model_params()
            if p is not None:
                if isinstance(p, (list, np.ndarray)):
                    params.append(p)
                else:
                    params.append([p])
        
        if not params:
            return None
        
        return np.array(params)

    def get_elastic_parameters(self) -> Optional[np.ndarray]:
        """
        Extract elastic model parameters from all curves.

        Returns
        -------
        np.ndarray or None
            Array of shape (n_curves, n_params) if all curves have parameters
        """
        params = []
        for curve in self.curves:
            p = curve.get_elastic_model_params()
            if p is not None:
                if isinstance(p, (list, np.ndarray)):
                    params.append(p)
                else:
                    params.append([p])
        
        if not params:
            return None
        
        return np.array(params)
