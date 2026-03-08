"""
No-op contact point detection.

This is used as a placeholder when no contact point detection is desired.
"""

from softmech.core.plugins import ContactPointDetector
import numpy as np

NAME = "None (No CP Detection)"
DESCRIPTION = "No contact point detection - returns None"
VERSION = "1.0.0"


class ContactPoint(ContactPointDetector):
    """
    No-op contact point detector that returns None.
    
    This is useful as a default/placeholder when contact point should not be calculated.
    """

    def calculate(self, x: np.ndarray, y: np.ndarray, curve=None) -> tuple:
        """
        Return None (no contact point detected).

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
        None or False
            Indicates no contact point was found
        """
        return None
