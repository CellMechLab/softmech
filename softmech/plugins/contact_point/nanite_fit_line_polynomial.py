"""Nanite-style contact point detection: piecewise line + polynomial fit."""

from ._nanite_base import NanitePOCBase

NAME = "Fit Line + Polynomial (Nanite)"
DESCRIPTION = "Estimate contact point using piecewise line + polynomial fit"
VERSION = "1.0.0"
DOI = ""


class ContactPointDetector(NanitePOCBase):
    METHOD = "fit_line_polynomial"
    METHOD_NAME = "Piecewise fit with line and polynomial"
