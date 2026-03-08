"""
Point of contact (POC) estimation routines.

These are based on well-known AFM contact point detection methods and
ported to avoid runtime dependencies on external projects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import lmfit
import numpy as np
from scipy.ndimage import uniform_filter1d


@dataclass(frozen=True)
class PocMethod:
    """Metadata for a POC method."""

    identifier: str
    name: str
    preprocessing: Tuple[str, ...]
    func: Callable[[np.ndarray, bool], Tuple[float, Optional[dict]]]


def compute_preproc_clip_approach(force: np.ndarray) -> np.ndarray:
    """Clip the approach part (discard the retract part)."""
    fg0 = np.array(force, copy=True)
    if fg0.size == 0:
        return fg0
    idmax = np.argmax(fg0)
    return fg0[:idmax]


def _normalize_force(force: np.ndarray) -> Tuple[np.ndarray, float, float]:
    fmin = np.min(force)
    fptp = np.max(force) - fmin
    if fptp == 0:
        return np.zeros_like(force), fmin, fptp
    return (force - fmin) / fptp, fmin, fptp


def _add_poc_details(details: dict, cp: int, y_min: float, y_max: float) -> None:
    details["plot poc"] = [[cp, cp], [y_min, y_max]]


def _scale_to_force(grad: np.ndarray, fmin: float, fmax: float) -> np.ndarray:
    gmin = np.min(grad)
    gptp = np.max(grad) - gmin
    if gptp == 0:
        return np.full_like(grad, fmin)
    return (grad - gmin) / gptp * (fmax - fmin) + fmin


def compute_poc(
    force: np.ndarray,
    method: str = "deviation_from_baseline",
    ret_details: bool = False,
) -> Tuple[int, Optional[dict]]:
    """Compute the contact point from force data."""
    if force.size == 0:
        if ret_details:
            return 0, {"method": method}
        return 0, None

    methods = _poc_method_map()
    if method not in methods:
        raise ValueError(f"Undefined POC method '{method}'!")

    mfunc = methods[method]
    fwork = np.array(force, copy=True)
    if "clip_approach" in mfunc.preprocessing:
        fwork = compute_preproc_clip_approach(fwork)

    cp, details = mfunc.func(fwork, ret_details)
    if np.isnan(cp):
        cp = fwork.size // 2

    cp = int(np.clip(cp, 0, max(0, fwork.size - 1)))
    if ret_details and details is not None:
        details["method"] = method
    return cp, details


def poc_deviation_from_baseline(force: np.ndarray, ret_details: bool = False):
    cp = np.nan
    details: Dict[str, object] = {}
    baseline = force[: int(force.size * 0.1)]
    if baseline.size:
        bl_avg = float(np.average(baseline))
        bl_rng = float(np.max(np.abs(baseline - bl_avg)) * 2)
        bl_dev = (force - bl_avg) > bl_rng
        maxid = int(np.argmax(bl_dev))
        if bl_dev[maxid]:
            cp = maxid
        if ret_details:
            x = [0, force.size - 1]
            details["plot force"] = [np.arange(force.size), force]
            details["plot baseline mean"] = [x, [bl_avg, bl_avg]]
            details["plot baseline threshold"] = [x, [bl_avg + bl_rng, bl_avg + bl_rng]]
            _add_poc_details(details, int(cp), float(np.min(force)), float(np.max(force)))
            details["norm"] = "force"
    return (cp, details) if ret_details else (cp, None)


def poc_fit_constant_line(force: np.ndarray, ret_details: bool = False):
    def model(params, x):
        d = params["d"]
        x0 = params["x0"]
        m = params["m"]
        one = d
        two = m * (x - x0) + d
        return np.maximum(one, two)

    def residual(params, x, data):
        return data - model(params, x)

    cp = np.nan
    details: Dict[str, object] = {}
    if force.size > 4:
        y, fmin, fptp = _normalize_force(force)
        x = np.arange(y.size)
        x0 = poc_frechet_direct_path(force, ret_details=False)[0]
        if np.isnan(x0):
            x0 = y.size // 2
        params = lmfit.Parameters()
        params.add("d", value=np.mean(y[:10]))
        params.add("x0", value=x0)
        params.add("m", value=(1 - y[int(x0)]) / max(1, (x.size - int(x0))))
        out = lmfit.minimize(residual, params, args=(x, y), method="nelder")
        if out.success:
            cp = int(out.params["x0"])
            if ret_details:
                details["plot force"] = [x, force]
                details["plot fit"] = [np.arange(force.size), model(out.params, x) * fptp + fmin]
                _add_poc_details(details, cp, float(fmin), float(fmin + fptp))
                details["norm"] = "force"
    return (cp, details) if ret_details else (cp, None)


def poc_fit_constant_polynomial(force: np.ndarray, ret_details: bool = False):
    def model(params, x):
        d = params["d"].value
        x0 = params["x0"].value
        a = params["a"].value
        b = params["b"].value
        c = params["c"].value
        x1 = x - x0
        curve = x1**3 / (a * x1**2 + b * x1 + c) + d
        curve[x1 <= 0] = d
        return curve

    def residual(params, x, data):
        curve = model(params, x)
        return data - curve

    cp = np.nan
    details: Dict[str, object] = {}
    if force.size > 6:
        y, fmin, fptp = _normalize_force(force)
        x = np.arange(y.size)
        x0 = poc_frechet_direct_path(force, ret_details=False)[0]
        if np.isnan(x0):
            x0 = y.size // 2
        params = lmfit.Parameters()
        params.add("d", value=np.mean(y[:10]))
        params.add("x0", value=x0)
        params.add("a", value=(y.size - x0), min=1e-3, max=100 * (y.size - x0))
        params.add("b", value=y.size, min=1e-3)
        params.add("c", value=0.5, min=1e-3)
        out = lmfit.minimize(residual, params, args=(x, y), method="nelder")
        if out.success:
            cp = int(out.params["x0"])
            if ret_details:
                details["plot force"] = [x, force]
                details["plot fit"] = [np.arange(force.size), model(out.params, x) * fptp + fmin]
                _add_poc_details(details, cp, float(fmin), float(fmin + fptp))
                details["norm"] = "force"
    return (cp, details) if ret_details else (cp, None)


def poc_fit_line_polynomial(force: np.ndarray, ret_details: bool = False):
    def model(params, x):
        d = params["d"].value
        x0 = params["x0"].value
        m = params["m"].value
        a = params["a"].value
        b = params["b"].value
        c = params["c"].value
        x1 = x - x0
        curve = m * x1 + d
        pos = x1 > 0
        curve[pos] += x1[pos] ** 3 / (a * x1[pos] ** 2 + b * x1[pos] + c)
        return curve

    def residual(params, x, data):
        curve = model(params, x)
        return data - curve

    cp = np.nan
    details: Dict[str, object] = {}
    if force.size > 7:
        y, fmin, fptp = _normalize_force(force)
        x = np.arange(y.size)
        x0 = poc_frechet_direct_path(force, ret_details=False)[0]
        if np.isnan(x0):
            x0 = y.size // 2
        params = lmfit.Parameters()
        params.add("d", value=np.mean(y[:10]))
        params.add("x0", value=x0)
        params.add("m", value=y[int(x0)] / max(1, int(x0)))
        params.add("a", value=(y.size - x0), min=1e-3, max=100 * (y.size - x0))
        params.add("b", value=y.size, min=1e-3)
        params.add("c", value=0.5, min=1e-3)
        out = lmfit.minimize(residual, params, args=(x, y), method="nelder")
        if out.success:
            cp = int(out.params["x0"])
            if ret_details:
                details["plot force"] = [x, force]
                details["plot fit"] = [np.arange(force.size), model(out.params, x) * fptp + fmin]
                _add_poc_details(details, cp, float(fmin), float(fmin + fptp))
                details["norm"] = "force"
    return (cp, details) if ret_details else (cp, None)


def poc_frechet_direct_path(force: np.ndarray, ret_details: bool = False):
    cp = np.nan
    details: Dict[str, object] = {}
    if force.size:
        x = np.linspace(0, 1, len(force), endpoint=True)
        fmin = float(force.min())
        fptp = float(force.max() - force.min())
        if fptp == 0:
            y = np.zeros_like(force, dtype=float)
        else:
            y = (force - fmin) / fptp
        alpha = -np.pi / 4
        yr = x * np.sin(alpha) + y * np.cos(alpha)
        cp = int(np.argmin(yr))
        if ret_details:
            details["plot normalized rotated force"] = [np.arange(len(force)), yr]
            details["plot poc"] = [[cp, cp], [float(yr.min()), float(yr.max())]]
            details["norm"] = "force-rotated"
    return (cp, details) if ret_details else (cp, None)


def poc_gradient_zero_crossing(force: np.ndarray, ret_details: bool = False):
    cp = np.nan
    details: Dict[str, object] = {}
    filtsize = max(5, int(force.size * 0.01))
    y = uniform_filter1d(force, size=filtsize)
    if y.size > 1:
        cutoff = y.size - np.argmax(y) + 10
        grad = np.gradient(y)[:-cutoff]
        if grad.size > 50:
            gradn = uniform_filter1d(grad, size=filtsize)
            thresh = 0.01 * np.max(gradn)
            gradpos = gradn <= thresh
            if np.sum(gradpos):
                cp = y.size - np.where(gradpos[::-1])[0][0] - cutoff + filtsize
                if ret_details:
                    grad_scaled = _scale_to_force(gradn, float(np.min(force)), float(np.max(force)))
                    x = np.arange(gradn.size)
                    details["plot force gradient"] = [x, grad_scaled]
                    details["plot threshold"] = [[x[0], x[-1]], [thresh, thresh]]
                    details["plot poc"] = [[int(cp), int(cp)], [float(grad_scaled.min()), float(grad_scaled.max())]]
                    details["norm"] = "force-gradient"
    return (cp, details) if ret_details else (cp, None)


def _poc_method_map() -> Dict[str, PocMethod]:
    methods: List[PocMethod] = [
        PocMethod(
            identifier="deviation_from_baseline",
            name="Deviation from baseline",
            preprocessing=("clip_approach",),
            func=poc_deviation_from_baseline,
        ),
        PocMethod(
            identifier="fit_constant_line",
            name="Piecewise fit with constant and line",
            preprocessing=("clip_approach",),
            func=poc_fit_constant_line,
        ),
        PocMethod(
            identifier="fit_constant_polynomial",
            name="Piecewise fit with constant and polynomial",
            preprocessing=("clip_approach",),
            func=poc_fit_constant_polynomial,
        ),
        PocMethod(
            identifier="fit_line_polynomial",
            name="Piecewise fit with line and polynomial",
            preprocessing=("clip_approach",),
            func=poc_fit_line_polynomial,
        ),
        PocMethod(
            identifier="frechet_direct_path",
            name="Frechet distance to direct path",
            preprocessing=("clip_approach",),
            func=poc_frechet_direct_path,
        ),
        PocMethod(
            identifier="gradient_zero_crossing",
            name="Gradient zero-crossing of indentation part",
            preprocessing=("clip_approach",),
            func=poc_gradient_zero_crossing,
        ),
    ]
    return {m.identifier: m for m in methods}


def list_poc_methods() -> Dict[str, str]:
    """Return available method identifiers and display names."""
    return {mid: meta.name for mid, meta in _poc_method_map().items()}
