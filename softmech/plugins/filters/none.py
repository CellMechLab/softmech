"""
No-op filter that passes data through unchanged.

This is used as a placeholder when no filtering is desired.
"""

from softmech.core.plugins import Filter
import numpy as np

NAME = "None (No Filter)"
DESCRIPTION = "Pass-through - no filtering applied"
VERSION = "1.0.0"


class Filter(Filter):
    """
    Pass-through filter that returns data unchanged.
    
    This is useful as a default/placeholder when no filtering is desired.
    """

    def calculate(self, x: np.ndarray, y: np.ndarray, curve=None) -> tuple:
        """
        Return data unchanged.

        Parameters
        ----------
        x : np.ndarray
            Displacement values (m)
        y : np.ndarray
            Force values (N)
        curve : Curve, optional
            Curve object (unused)

        Returns
        -------
        tuple
            (x, y) unchanged
        """
        return x, y
