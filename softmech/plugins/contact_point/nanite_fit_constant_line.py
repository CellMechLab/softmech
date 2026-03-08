"""Nanite-style contact point detection: piecewise constant + line fit."""

from ._nanite_base import NanitePOCBase

NAME = "Fit Constant + Line (Nanite)"
DESCRIPTION = "Estimate contact point using piecewise constant + line fit"
VERSION = "1.0.0"
DOI = ""


class ContactPointDetector(NanitePOCBase):
    METHOD = "fit_constant_line"
    METHOD_NAME = "Piecewise fit with constant and line"
