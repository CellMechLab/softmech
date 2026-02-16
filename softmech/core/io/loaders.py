"""
Data loaders for AFM measurements.

Supports JSON and HDF5 formats.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


def load_json(filename: str) -> Dict[str, Any]:
    """
    Load AFM curves from JSON file.

    Expected format:
    {
        "curves": [
            {
                "Z": [...],
                "F": [...],
                "spring_constant": 0.01,
                "tip": {
                    "geometry": "sphere",
                    "radius": 1e-6
                },
                "metadata": {...}
            },
            ...
        ]
    }

    Parameters
    ----------
    filename : str
        Path to JSON file

    Returns
    -------
    dict
        Loaded data structure
    """
    with open(filename, "r") as f:
        data = json.load(f)

    logger.info(f"Loaded JSON file: {filename}")
    return data


def load_hdf5(filename: str) -> Dict[str, Any]:
    """
    Load AFM curves from HDF5 file.

    Expected structure:
    /
    ├── curve1/
    │   ├── attributes: spring_constant, tip geometry
    │   ├── segment0/
    │   │   ├── Force
    │   │   ├── Z
    │   ├── cp (optional)
    ├── curve2/
    ...

    Parameters
    ----------
    filename : str
        Path to HDF5 file

    Returns
    -------
    dict
        Loaded data structure
    """
    try:
        import h5py
    except ImportError:
        raise ImportError("h5py required for HDF5 support")

    data = {"curves": []}

    with h5py.File(filename, "r") as f:
        for curve_name in f.keys():
            curve_group = f[curve_name]

            # Read attributes
            attrs = dict(curve_group.attrs)

            # Find first segment with data
            segment_name = None
            for key in curve_group.keys():
                if key.startswith("segment"):
                    segment_name = key
                    break

            if segment_name is None:
                logger.warning(f"No segment found in {curve_name}")
                continue

            segment = curve_group[segment_name]

            # Read Force and Z
            if "Force" not in segment or "Z" not in segment:
                logger.warning(f"Missing Force or Z in {curve_name}/{segment_name}")
                continue

            force = np.array(segment["Force"])
            z = np.array(segment["Z"])

            # Build curve dict
            curve_dict = {
                "Z": z.tolist(),
                "F": force.tolist(),
                "spring_constant": float(attrs.get("spring_constant", 1.0)),
                "tip": {
                    "geometry": str(attrs.get("tip_geometry", "sphere")),
                    "radius": float(attrs.get("tip_radius", 1e-6)) if "tip_radius" in attrs else None,
                    "angle": float(attrs.get("tip_angle", 45.0)) if "tip_angle" in attrs else None,
                },
                "metadata": {k: v for k, v in attrs.items() if not k.startswith("tip_")},
            }

            # Optional: read contact point if available
            if "cp" in curve_group:
                cp_data = curve_group["cp"][()]
                curve_dict["contact_point"] = [float(cp_data[0]), float(cp_data[1])]

            data["curves"].append(curve_dict)

    logger.info(f"Loaded HDF5 file: {filename} ({len(data['curves'])} curves)")
    return data


def load(filename: str) -> Dict[str, Any]:
    """
    Auto-detect format and load AFM data.

    Parameters
    ----------
    filename : str
        Path to data file

    Returns
    -------
    dict
        Loaded data structure

    Raises
    ------
    ValueError
        If file format not recognized
    """
    path = Path(filename)

    if path.suffix.lower() == ".json":
        return load_json(filename)
    elif path.suffix.lower() in (".h5", ".hdf5"):
        return load_hdf5(filename)
    else:
        raise ValueError(f"Unknown file format: {path.suffix}")
