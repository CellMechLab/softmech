"""
Automatic threshold-based contact point detection.

Uses statistical analysis of force curve derivatives to identify the contact point.
"""

from softmech.core.plugins import ContactPointDetector
import numpy as np

NAME = "Auto Threshold"
DESCRIPTION = "Automatic contact point detection via multi-level thresholding"
VERSION = "1.0.0"
DOI = ""


class ContactPointDetector(ContactPointDetector):
    """
    Automatic contact point detection using thresholding.

    Analyzes the force curve to find a linear baseline region, then identifies
    where the curve deviates from this baseline (contact point).

    Parameters
    ----------
    zero_range : float
        Distance from curve start to use for baseline determination (nm)
    """

    # Parameters
    zero_range: float = 500.0  # nanometers

    # Constraints
    zero_range_min: float = 1.0
    zero_range_max: float = 9999.0

    def calculate(self, x: np.ndarray, y: np.ndarray, curve=None) -> tuple:
        """
        Detect contact point using automatic thresholding.

        Parameters
        ----------
        x : np.ndarray
            Displacement (Z) values (m)
        y : np.ndarray
            Force values (N)
        curve : optional
            Curve metadata

        Returns
        -------
        tuple
            (z_contact, f_contact) or False if detection fails
        """
        zero_range = self.get_parameter("zero_range") * 1e-9

        # Work with a copy
        work_y = np.copy(y)

        # Find baseline region
        x_target = np.min(x) + zero_range
        j_target = np.argmin(np.abs(x - x_target))

        # Determine data direction and fit baseline
        if x[0] < x[-1]:
            # X increasing: use first part as baseline
            x_lin = x[:j_target]
            y_lin = work_y[:j_target]
        else:
            # X decreasing: use last part as baseline
            x_lin = x[j_target:]
            y_lin = work_y[j_target:]

        # Fit linear baseline
        try:
            m, q = np.polyfit(x_lin, y_lin, 1)
        except Exception:
            return False

        # Remove baseline trend
        detrended = work_y - (m * x + q)

        # Find gradient crossings
        differences = (detrended[1:] + detrended[:-1]) / 2.0
        midpoints = np.unique(differences)
        midpoints.sort()

        # Count zero-crossings at different thresholds
        positive_midpoints = midpoints[midpoints > 0]

        if len(positive_midpoints) == 0:
            return False

        crossings = []
        for threshold in positive_midpoints:
            n_cross = np.sum(
                np.bitwise_and((detrended[1:] > threshold), (detrended[:-1] < threshold))
            )
            crossings.append(n_cross)

        crossings = np.array(crossings)

        # Find threshold with exactly 1 crossing
        candidates = np.where(crossings == 1)[0]

        if len(candidates) == 0:
            return False

        # Use first candidate
        inflection = positive_midpoints[candidates[0]]
        j_cp_guess = np.argmin(np.abs(differences - inflection)) + 1

        # Return contact point
        x_cp = x[j_cp_guess]
        y_cp = y[j_cp_guess]

        return (x_cp, y_cp)
