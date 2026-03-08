"""Nanite-style contact point detection: deviation from baseline."""

from ._nanite_base import NanitePOCBase

NAME = "Deviation from Baseline (Nanite)"
DESCRIPTION = "Estimate contact point using deviation from baseline"
VERSION = "1.0.0"
DOI = "1010.dede.te"


class ContactPointDetector(NanitePOCBase):
    METHOD = "deviation_from_baseline"
    METHOD_NAME = "Deviation from baseline"
