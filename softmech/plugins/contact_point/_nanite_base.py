"""Shared base class for nanite-inspired POC plugins."""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from softmech.core.algorithms import poc
from softmech.core.plugins import ContactPointDetector


class NanitePOCBase(ContactPointDetector):
    """Base class for nanite-inspired point-of-contact plugins."""

    METHOD: str = ""
    METHOD_NAME: str = ""

    def __init__(self):
        super().__init__()
        self.last_details: Optional[dict] = None

    def calculate(self, x: np.ndarray, y: np.ndarray, curve=None) -> Tuple[float, float]:
        cp_index, details = poc.compute_poc(y, method=self.METHOD, ret_details=True)
        self.last_details = details
        if details is not None:
            details["poc_index"] = cp_index

        if x.size == 0 or y.size == 0:
            return float("nan"), float("nan")

        cp_index = int(np.clip(cp_index, 0, min(len(x), len(y)) - 1))
        return float(x[cp_index]), float(y[cp_index])
