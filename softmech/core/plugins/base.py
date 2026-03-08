"""
Base classes for SoftMech plugins.

All plugins inherit from one of these classes. Parameters are defined as
type-annotated class variables, which can be introspected by UIs (magicgui, CLI, etc.)
without Qt or other UI framework dependencies.

Example plugin definition:

    from softmech.core.plugins import Filter
    import numpy as np

    class MyFilter(Filter):
        '''Custom filter'''
        
        window_size: float = 25.0  # nanometers
        order: int = 3
        
        window_size_min: float = 1.0
        window_size_max: float = 500.0
        
        def calculate(self, x, y, curve=None):
            # Use self.window_size and self.order
            # Return filtered (x, y)
            pass
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple, get_type_hints, Optional
import numpy as np


class PluginBase(ABC):
    """
    Base class for all SoftMech plugins.

    Parameters are defined as type-annotated class variables with default values.
    UIs (magicgui, CLI, Python API) can introspect these automatically.

    Attributes
    ----------
    None (subclasses define their own parameters as class variables)

    Methods
    -------
    get_parameter(name): Get parameter value
    set_parameter(name, value): Set parameter value
    get_parameters_dict(): Get all parameters as dictionary
    calculate(x, y, curve=None): Perform computation (must override)
    """

    def __init__(self):
        """Initialize plugin - captures parameters from type hints."""
        self._initialize_parameters()

    def _initialize_parameters(self) -> None:
        """
        Introspect class annotations and set up instance parameters.

        This allows plugins to define parameters as type-annotated class variables,
        which are automatically initialized as instance attributes.
        """
        hints = get_type_hints(self.__class__)
        for name, type_hint in hints.items():
            # Skip private/internal attributes
            if name.startswith("_"):
                continue

            # Get default value from class if it exists
            if hasattr(self.__class__, name):
                value = getattr(self.__class__, name)
            else:
                # If no default, set to None (UI can make it required)
                value = None

            setattr(self, name, value)

    def get_parameter(self, name: str) -> Any:
        """
        Get a parameter value by name.

        Parameters
        ----------
        name : str
            Parameter name

        Returns
        -------
        Any
            Current parameter value

        Raises
        ------
        KeyError
            If parameter does not exist
        """
        if not hasattr(self, name):
            raise KeyError(f"Unknown parameter: {name}")
        return getattr(self, name)

    def set_parameter(self, name: str, value: Any) -> None:
        """
        Set a parameter value.

        Parameters
        ----------
        name : str
            Parameter name
        value : Any
            New value

        Raises
        ------
        KeyError
            If parameter does not exist
        """
        if not hasattr(self, name):
            raise KeyError(f"Unknown parameter: {name}")
        setattr(self, name, value)

    def get_parameters_dict(self) -> Dict[str, Any]:
        """
        Get all non-private parameters as a dictionary.

        Useful for serialization (JSON, YAML) and UI binding.

        Returns
        -------
        dict
            {parameter_name: current_value}
        """
        hints = get_type_hints(self.__class__)
        return {
            name: getattr(self, name)
            for name in hints
            if not name.startswith("_")
            and not name.endswith("_min")
            and not name.endswith("_max")
        }

    def set_parameters_dict(self, params: Dict[str, Any]) -> None:
        """
        Set multiple parameters from a dictionary.

        Parameters
        ----------
        params : dict
            {parameter_name: value} dictionary
        """
        for name, value in params.items():
            self.set_parameter(name, value)

    @abstractmethod
    def calculate(self, x: np.ndarray, y: np.ndarray, curve=None) -> Any:
        """
        Perform the plugin's main computation.

        Must be overridden by subclasses.

        Parameters
        ----------
        x : np.ndarray
            Input x-data (typically depth or indentation)
        y : np.ndarray
            Input y-data (typically force)
        curve : optional
            Optional curve object with metadata (spring_constant, tip geometry, etc.)

        Returns
        -------
        Depends on plugin type:
        - Filter: (x_filtered, y_filtered) tuple
        - ContactPointDetector: (x_contact, y_contact) tuple
        - ForceModel/ElasticModel: fitted_parameters (list or dict)
        - Exporter: None (side effect: writes file)

        Return False or None if computation fails.
        """
        pass


class Filter(PluginBase):
    """
    Base class for data preprocessing filters.

    Filters smooth, clean, or transform raw force-displacement curves.

    Subclasses must override calculate() to return (x_filtered, y_filtered).
    """

    def calculate(
        self, x: np.ndarray, y: np.ndarray, curve=None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply filter to curve data.

        Parameters
        ----------
        x : np.ndarray
            Displacement values
        y : np.ndarray
            Force values
        curve : optional
            Curve metadata

        Returns
        -------
        tuple
            (x_filtered, y_filtered) - same length as input
        """
        pass


class ContactPointDetector(PluginBase):
    """
    Base class for detecting the contact point between AFM tip and sample.

    The contact point (z_contact, F_contact) marks where the tip first touches
    the sample surface.

    Subclasses must override calculate() to return the contact point coordinates.
    """

    def calculate(self, x: np.ndarray, y: np.ndarray, curve=None) -> Tuple[float, float]:
        """
        Detect contact point on force curve.

        Parameters
        ----------
        x : np.ndarray
            Displacement values (Z)
        y : np.ndarray
            Force values (F)
        curve : optional
            Curve object with metadata

        Returns
        -------
        tuple
            (z_contact, F_contact) - coordinates of contact point
        """
        pass


class ForceModel(PluginBase):
    """
    Base class for modeling force-indentation relationships.

    Force models (e.g., Hertz) fit the F(δ) curve to extract mechanical
    properties like Young's modulus.

    Parameters
    ----------
    min_indentation_depth : float
        Minimum indentation depth (δ) for fitting region in nanometers (nm).
        Range: 0-10000 nm (0-10 μm). If 0, uses minimum available data.
    max_indentation_depth : float
        Maximum indentation depth (δ) for fitting region in nanometers (nm).
        Range: 0-10000 nm (0-10 μm). If 0, uses maximum available data.

    Subclasses must implement:
    - calculate(): Fit model to data, return parameters
    - theory(): Generate theoretical curve for given parameters
    """

    # Fitting region parameters (in nanometers, 0-10000 nm typical range)
    min_indentation_depth: float = 0.0  # 0 means use minimum available
    max_indentation_depth: float = 0.0  # 0 means use maximum available

    def _get_fitting_region(self, x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract the fitting region from indentation data based on region parameters.

        Parameters are in nanometers. Input x data is assumed to be in meters (SI units)
        and is converted for comparison.

        Parameters
        ----------
        x : np.ndarray
            Indentation depth values (meters)
        y : np.ndarray
            Force values

        Returns
        -------
        tuple
            (x_region, y_region) - Data within the specified fitting region
        """
        x = np.asarray(x)
        y = np.asarray(y)

        # Get region bounds in nanometers
        x_min_nm = self.get_parameter("min_indentation_depth")
        x_max_nm = self.get_parameter("max_indentation_depth")

        # Convert indentation data to nanometers for comparison
        x_nm = x * 1e9  # Convert meters to nanometers

        # If min is 0 or not set, use data minimum
        if x_min_nm <= 0:
            x_min_nm = np.nanmin(x_nm) if np.all(np.isfinite(x_nm)) else 0.0

        # If max is 0 or not set, use data maximum
        if x_max_nm <= 0:
            x_max_nm = np.nanmax(x_nm) if np.all(np.isfinite(x_nm)) else np.inf

        # Create boolean mask for fitting region
        mask = (x_nm >= x_min_nm) & (x_nm <= x_max_nm)

        return x[mask], y[mask]

    def calculate(self, x: np.ndarray, y: np.ndarray, curve=None) -> Any:
        """
        Fit force model to indentation data.

        Parameters
        ----------
        x : np.ndarray
            Indentation depth (δ)
        y : np.ndarray
            Force (F)
        curve : optional
            Curve object with tip geometry, spring_constant, etc.

        Returns
        -------
        Any
            Fitted parameters (list or dict, model-specific)
        """
        pass

    @abstractmethod
    def theory(self, x: np.ndarray, *params, curve=None) -> np.ndarray:
        """
        Generate theoretical force curve for given parameters.

        Used for visualization and fitting.

        Parameters
        ----------
        x : np.ndarray
            Indentation depth values for which to compute theory
        *params
            Fitted parameters from calculate()
        curve : optional
            Curve object with metadata

        Returns
        -------
        np.ndarray
            Theoretical force values
        """
        pass


class ElasticModel(PluginBase):
    """
    Base class for modeling elasticity (Young's modulus) vs. indentation depth.

    Elastic models fit the E(δ) relationship derived from elasticity spectra.

    Subclasses must implement:
    - calculate(): Fit model to elasticity spectra data
    - theory(): Generate theoretical E(δ) for given parameters
    """

    def calculate(self, x: np.ndarray, y: np.ndarray, curve=None) -> Any:
        """
        Fit elastic model to elasticity spectra data.

        Parameters
        ----------
        x : np.ndarray
            Indentation depth (δ)
        y : np.ndarray
            Elastic modulus (E)
        curve : optional
            Curve object

        Returns
        -------
        Any
            Fitted parameters (list or dict, model-specific)
        """
        pass

    @abstractmethod
    def theory(self, x: np.ndarray, *params, curve=None) -> np.ndarray:
        """
        Generate theoretical elasticity curve.

        Parameters
        ----------
        x : np.ndarray
            Indentation depth values
        *params
            Fitted parameters
        curve : optional
            Curve object

        Returns
        -------
        np.ndarray
            Theoretical E values
        """
        pass


class Exporter(PluginBase):
    """
    Base class for exporting processed results.

    Exporters save analysis results (parameters, curves, statistics) to files.

    Subclasses must implement:
    - export(): Write results to file
    """

    @abstractmethod
    def export(self, filename: str, data: Any) -> None:
        """
        Export analysis results to file.

        Parameters
        ----------
        filename : str
            Output file path
        data : Any
            Data to export (structure depends on exporter)

        Returns
        -------
        None
        """
        pass

    def preview(self, ax, data: Any) -> None:
        """
        Optional: Generate preview visualization (matplotlib axes).

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Axes object for plotting
        data : Any
            Data to visualize

        Returns
        -------
        None
        """
        pass
