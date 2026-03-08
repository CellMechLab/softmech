"""
Savitzky-Golay filter for AFM curve preprocessing.

Smoothes force-displacement curves while preserving features like steps and peaks.
"""

from softmech.core.plugins import Filter
from scipy.signal import savgol_filter
import numpy as np

NAME = "Savitzky-Golay"
DESCRIPTION = "Savitzky-Golay smoothing filter - preserves steps and peaks"
VERSION = "1.1.0"
DOI = "https://doi.org/10.1038/s41592-019-0686-2"


class Filter(Filter):
    """
    Savitzky-Golay smoothing filter.

    Applies polynomial smoothing to AFM curves. Window size is specified in
    nanometers but is converted to points based on the data spacing.

    Parameters
    ----------
    window_size : float
        Window size in nanometers (will be converted to odd number of points)
    polyorder : int
        Order of polynomial (must be < window_size in points)
    """

    # Parameters as type-annotated class variables
    window_size: float = 25.0  # nanometers
    polyorder: int = 3

    # Constraint hints (optional, used by UI)
    window_size_min: float = 1.0
    window_size_max: float = 500.0
    polyorder_min: int = 1
    polyorder_max: int = 7

    def calculate(self, x: np.ndarray, y: np.ndarray, curve=None) -> tuple:
        """
        Apply Savitzky-Golay filter to curve data.

        Parameters
        ----------
        x : np.ndarray
            Displacement values (m)
        y : np.ndarray
            Force values (N)
        curve : optional
            Curve metadata (unused here)

        Returns
        -------
        tuple
            (x_filtered, y_filtered)
        """
        # Get current parameters
        window_nm = self.get_parameter("window_size")
        polyorder = self.get_parameter("polyorder")

        # Convert window size from nm to points
        x_window_m = window_nm * 1e-9
        x_step = np.mean(np.diff(x))
        window_points = int(np.round(x_window_m / x_step))

        # Ensure window is odd
        if window_points % 2 == 0:
            window_points += 1

        # Validate parameters
        if window_points < 3:
            window_points = 3
        if polyorder >= window_points:
            polyorder = window_points - 1

        # Apply filter
        try:
            y_filtered = savgol_filter(y, window_points, polyorder)
            return x, y_filtered
        except Exception as e:
            # Return False if filtering fails
            print(f"SavGol filter error: {e}")
            return False
