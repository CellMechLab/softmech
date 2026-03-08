"""
Spectral analysis algorithms for indentation and elasticity calculations.
"""

import numpy as np
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d
import logging

logger = logging.getLogger(__name__)


def calculate_indentation(curve, zero_force: bool = True) -> None:
    """
    Calculate indentation depth from contact point and spring constant.

    δ = (Z - Z_cp) - (F - F_cp) / k

    Parameters
    ----------
    curve : Curve
        Curve object with contact point set
    zero_force : bool
        If True, set force to zero at contact point

    Raises
    ------
    ValueError
        If contact point not set
    """
    contact_point = curve.get_contact_point()
    if contact_point is None:
        raise ValueError("Contact point must be set before calculating indentation")

    z_cp, f_cp = contact_point
    z, f = curve.get_current_data()

    # Find index closest to contact point
    j_contact = np.argmin((z - z_cp) ** 2)

    # Calculate indentation and force from contact
    if zero_force:
        f_ind = f[j_contact:] - f_cp
    else:
        f_ind = f[j_contact:]

    z_ind = z[j_contact:] - z_cp
    delta = z_ind - f_ind / curve.spring_constant

    curve.set_indentation_data(delta, f_ind)
    logger.debug(f"Calculated indentation for curve {curve.index}: {len(delta)} points")


def calculate_elasticity_spectra(
    curve,
    window_size: int = 5,
    order: int = 3,
    interpolate: bool = True,
) -> None:
    """
    Calculate dynamic indentation modulus from elasticity spectra.

    E(δ) = (3 / 8√(πA)) * (dF/dδ)

    where A(δ) depends on tip geometry.

    Parameters
    ----------
    curve : Curve
        Curve with indentation data and tip geometry set
    window_size : int
        Savitzky-Golay window size (points)
    order : int
        Savitzky-Golay polynomial order
    interpolate : bool
        If True, interpolate to regular depth spacing

    Raises
    ------
    ValueError
        If indentation data not available or invalid
    """
    delta, f = curve.get_indentation_data()

    if delta is None or len(delta) < 2:
        logger.warning(f"Invalid indentation data for curve {curve.index}")
        return

    # Prepare x and y for derivative
    if interpolate:
        # Interpolate to regular spacing
        f_interp = interp1d(delta, f, kind="linear", fill_value="extrapolate")
        delta_min = np.max([1.0e-9, np.min(delta)])
        delta_max = np.max(delta)
        delta_new = np.arange(delta_min, delta_max, 1.0e-9)
        f_new = f_interp(delta_new)

        x = delta_new
        y = f_new
        ddt = 1.0e-9
    else:
        x = delta[1:]
        y = f[1:]
        ddt = (delta[-1] - delta[1]) / (len(delta) - 2)

    # Ensure window is valid and odd
    window = window_size if window_size % 2 == 1 else window_size + 1
    if order >= window:
        order = window - 1

    if len(y) <= window:
        logger.warning(f"Indentation too short for elasticity calculation: {len(y)} < {window}")
        return

    # Calculate derivative
    try:
        ddf = savgol_filter(y, window, order, delta=ddt, deriv=1)
    except Exception as e:
        logger.error(f"Error calculating derivative: {e}")
        return

    # Calculate contact area from tip geometry
    geom = curve.tip_geometry
    try:
        if geom.geometry_type == "sphere":
            # A = π * R * δ
            a_radius = np.sqrt(x * geom.radius)
        elif geom.geometry_type == "cylinder":
            # A = 2 * R * δ
            a_radius = geom.radius
        elif geom.geometry_type == "cone":
            # A = (2δ/tan(α)) / π
            angle_rad = geom.angle * np.pi / 180.0
            a_radius = 2 * x / np.tan(angle_rad) / np.pi
        elif geom.geometry_type == "pyramid":
            # Bilodeau formula
            angle_rad = geom.angle * np.pi / 180.0
            a_radius = 0.709 * x * np.tan(angle_rad)
        else:
            logger.error(f"Unknown tip geometry: {geom.geometry_type}")
            return
    except Exception as e:
        logger.error(f"Error calculating contact area: {e}")
        return

    # Calculate elasticity: E = (3 / 8√(πA)) * (dF/dδ)
    coeff = 3 / 8 / np.sqrt(np.pi * a_radius)
    e_values = coeff * ddf

    # Remove edge artifacts from Savitzky-Golay
    dwin = int((window - 1) / 2)
    x_final = x[dwin:-dwin]
    e_final = e_values[dwin:-dwin]

    curve.set_elasticity_spectra(x_final, e_final)
    logger.debug(
        f"Calculated elasticity spectra for curve {curve.index}: "
        f"{len(x_final)} points, E range: {np.min(e_final):.2e} - {np.max(e_final):.2e} Pa"
    )
