"""
Data loaders for AFM measurements.

Supports JSON and HDF5 formats.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, TYPE_CHECKING
import numpy as np
import logging
from datetime import datetime

if TYPE_CHECKING:
    from softmech.core.data import Dataset

logger = logging.getLogger(__name__)


def _serialize_params(params: Any) -> Optional[str]:
    """Serialize fitted parameters to JSON-safe string."""
    if params is None:
        return None
    try:
        return json.dumps(params)
    except Exception:
        return None


def _deserialize_params(value: Any) -> Optional[Any]:
    """Deserialize fitted parameters from JSON-safe string."""
    if value is None:
        return None
    try:
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return json.loads(value)
    except Exception:
        return None


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
            # Handle tip radius/angle with None-safety
            tip_radius = attrs.get("tip_radius", 1e-6)
            tip_angle = attrs.get("tip_angle", 45.0)
            try:
                tip_radius = float(tip_radius) if tip_radius is not None else None
            except (ValueError, TypeError):
                tip_radius = 1e-6
            try:
                tip_angle = float(tip_angle) if tip_angle is not None else None
            except (ValueError, TypeError):
                tip_angle = 45.0

            curve_dict = {
                "Z": z.tolist(),
                "F": force.tolist(),
                "spring_constant": float(attrs.get("spring_constant", 1.0)) if attrs.get("spring_constant") is not None else 1.0,
                "tip": {
                    "geometry": str(attrs.get("tip_geometry", "sphere")),
                    "radius": tip_radius,
                    "angle": tip_angle,
                },
                "metadata": {k: v for k, v in attrs.items() if not k.startswith("tip_")},
                "is_outlier": bool(attrs.get("is_outlier", False)),  # Backwards compatible default
            }

            # Optional: read fitted force-model parameters if available
            if "force_model_params_json" in attrs:
                params = _deserialize_params(attrs.get("force_model_params_json"))
                if params is not None:
                    curve_dict["force_model_params"] = params

            # Optional: read contact point if available
            if "cp" in curve_group:
                try:
                    cp_data = curve_group["cp"][()]
                    if cp_data is not None and len(cp_data) >= 2:
                        cp0 = float(cp_data[0]) if cp_data[0] is not None else 0.0
                        cp1 = float(cp_data[1]) if cp_data[1] is not None else 0.0
                        curve_dict["contact_point"] = [cp0, cp1]
                except (ValueError, TypeError, IndexError):
                    logger.warning(f"Could not read contact point from {curve_name}")

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


def save_hdf5(filename: str, dataset: 'Dataset') -> None:
    """
    Save Dataset to HDF5 file with outlier flags.

    Structure:
    /
    ├── curve0/
    │   ├── attributes: spring_constant, tip geometry, is_outlier
    │   ├── segment0/
    │   │   ├── Force
    │   │   ├── Z
    │   ├── cp (if available)
    ├── curve1/
    ...

    Parameters
    ----------
    filename : str
        Path to output HDF5 file
    dataset : Dataset
        Dataset to save
    """
    try:
        import h5py
    except ImportError:
        raise ImportError("h5py required for HDF5 support")

    with h5py.File(filename, "w") as f:
        for i, curve in enumerate(dataset):
            curve_name = f"curve{i}"
            curve_group = f.create_group(curve_name)

            # Write attributes
            curve_group.attrs["spring_constant"] = curve.spring_constant
            curve_group.attrs["tip_geometry"] = curve.tip_geometry.geometry_type
            
            if curve.tip_geometry.radius is not None:
                curve_group.attrs["tip_radius"] = curve.tip_geometry.radius
            if curve.tip_geometry.angle is not None:
                curve_group.attrs["tip_angle"] = curve.tip_geometry.angle
            
            # Write outlier flag
            curve_group.attrs["is_outlier"] = curve.is_outlier

            # Write fitted force-model parameters when available
            params_json = _serialize_params(curve.get_force_model_params())
            if params_json is not None:
                curve_group.attrs["force_model_params_json"] = params_json
            
            # Write metadata
            for key, value in curve.metadata.items():
                try:
                    curve_group.attrs[key] = value
                except (TypeError, ValueError):
                    logger.warning(f"Could not save metadata key '{key}' for curve {i}")

            # Write segment data
            segment = curve_group.create_group("segment0")
            Z, F = curve.get_current_data()
            segment.create_dataset("Z", data=Z)
            segment.create_dataset("Force", data=F)

            # Write contact point if available
            cp = curve.get_contact_point()
            if cp is not None:
                curve_group.create_dataset("cp", data=np.array(cp))

    logger.info(f"Saved HDF5 file: {filename} ({len(dataset)} curves)")


def save_json(filename: str, dataset: 'Dataset') -> None:
    """
    Save Dataset to JSON file with outlier flags.

    Parameters
    ----------
    filename : str
        Path to output JSON file
    dataset : Dataset
        Dataset to save
    """
    data = {
        "name": dataset.name,
        "created": dataset.created.isoformat() if hasattr(dataset, "created") else datetime.now().isoformat(),
        "curves": []
    }

    for curve in dataset:
        Z, F = curve.get_current_data()
        curve_dict = {
            "Z": Z.tolist(),
            "F": F.tolist(),
            "spring_constant": curve.spring_constant,
            "tip": {
                "geometry": curve.tip_geometry.geometry_type,
                "radius": curve.tip_geometry.radius,
                "angle": curve.tip_geometry.angle,
            },
            "metadata": curve.metadata,
            "is_outlier": curve.is_outlier,
        }

        # Add fitted force-model parameters when available
        force_model_params = curve.get_force_model_params()
        if force_model_params is not None:
            curve_dict["force_model_params"] = force_model_params
        
        # Add contact point if available
        cp = curve.get_contact_point()
        if cp is not None:
            curve_dict["contact_point"] = list(cp)
        
        data["curves"].append(curve_dict)

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved JSON file: {filename} ({len(dataset)} curves)")


def save(filename: str, dataset: 'Dataset') -> None:
    """
    Auto-detect format and save Dataset.

    Parameters
    ----------
    filename : str
        Path to output file
    dataset : Dataset
        Dataset to save

    Raises
    ------
    ValueError
        If file format not recognized
    """
    path = Path(filename)

    if path.suffix.lower() == ".json":
        save_json(filename, dataset)
    elif path.suffix.lower() in (".h5", ".hdf5"):
        save_hdf5(filename, dataset)
    else:
        raise ValueError(f"Unknown file format: {path.suffix}")
