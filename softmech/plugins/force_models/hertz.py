"""
Hertz contact mechanics model for force-indentation fitting.

Fits F(δ) curves using Hertz contact theory, which models elastic contact
between the AFM tip and sample.
"""

from softmech.core.plugins import ForceModel
from scipy.optimize import curve_fit
import numpy as np
import logging
from typing import Any

logger = logging.getLogger(__name__)

NAME = "Hertz"
DESCRIPTION = "Hertz contact mechanics model for AFM indentation fitting"
VERSION = "1.1.0"
DOI = ""


class ForceModel(ForceModel):
    """
    Hertz contact mechanics model.

    Fits force-indentation data using the Hertz model. The model depends on
    tip geometry (sphere, cone, cylinder, pyramid).

    Parameters
    ----------
    poisson : float
        Poisson's ratio of the sample (-1 to 0.5)
    """

    # Parameters
    poisson: float = 0.5

    # Constraints
    poisson_min: float = -1.0
    poisson_max: float = 0.5

    def theory(self, x: np.ndarray, elastic: float, curve=None) -> np.ndarray:
        """
        Generate theoretical Hertz force-indentation curve.

        Parameters
        ----------
        x : np.ndarray
            Indentation depth δ (m)
        elastic : float
            Young's modulus E (Pa)
        curve : optional
            Curve object with tip geometry

        Returns
        -------
        np.ndarray
            Theoretical force values
        """
        if curve is None:
            raise ValueError("Curve object required for Hertz theory")

        poisson = self.get_parameter("poisson")
        geom = curve.tip_geometry

        if geom.geometry_type == "sphere":
            # F = (4/3) * (E / (1-ν²)) * √(R*δ³)
            R = geom.radius
            return (4.0 / 3.0) * (elastic / (1 - poisson**2)) * np.sqrt(R * x**3)

        elif geom.geometry_type == "pyramid":
            # Bilodeau formula
            angle_rad = geom.angle * np.pi / 180.0
            return (
                0.7453
                * (elastic * np.tan(angle_rad) / (1 - poisson**2))
                * x**2
            )

        elif geom.geometry_type == "cylinder":
            # F = 2 * (E / (1-ν²)) * R * δ
            R = geom.radius
            return (2.0) * (elastic / (1 - poisson**2)) * R * x

        elif geom.geometry_type == "cone":
            # F = 2 * tan(α) * E / (π(1-ν²)) * δ²
            angle_rad = geom.angle * np.pi / 180.0
            return (
                (2.0 * np.tan(angle_rad) * elastic)
                / (np.pi * (1 - poisson**2))
                * x**2
            )

        else:
            raise ValueError(f"Unsupported tip geometry: {geom.geometry_type}")

    def calculate(self, x: np.ndarray, y: np.ndarray, curve=None) -> Any:
        """
        Fit Hertz model to indentation data.

        Parameters
        ----------
        x : np.ndarray
            Indentation depth δ (m)
        y : np.ndarray
            Force F (N)
        curve : optional
            Curve with tip geometry

        Returns
        -------
        list
            [elastic_modulus] or False if fitting fails
        """
        if curve is None:
            logger.error("Curve object required for Hertz fitting")
            return False

        if len(x) < 5:
            logger.warning("Insufficient data points for fitting")
            return False

        try:
            # Fit with initial guess
            def theory_wrapper(x_fit, E):
                return self.theory(x_fit, E, curve=curve)

            popt, _ = curve_fit(theory_wrapper, x, y, p0=[1e3], maxfev=1000)
            return list(popt)

        except RuntimeError as e:
            logger.error(f"Hertz fitting failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in Hertz fitting: {e}")
            return False
