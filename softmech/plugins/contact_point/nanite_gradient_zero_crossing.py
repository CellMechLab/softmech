"""Nanite-style contact point detection: gradient zero crossing."""

from ._nanite_base import NanitePOCBase

NAME = "Gradient Zero Crossing (Nanite)"
DESCRIPTION = "Estimate contact point using gradient zero crossing"
VERSION = "1.0.0"
DOI = ""


class ContactPointDetector(NanitePOCBase):
    METHOD = "gradient_zero_crossing"
    METHOD_NAME = "Gradient zero-crossing of indentation part"
