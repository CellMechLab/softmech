"""Nanite-style contact point detection: piecewise constant + polynomial fit."""

from ._nanite_base import NanitePOCBase

NAME = "Fit Constant + Polynomial (Nanite)"
DESCRIPTION = "Estimate contact point using piecewise constant + polynomial fit"
VERSION = "1.0.0"
DOI = ""


class ContactPointDetector(NanitePOCBase):
    METHOD = "fit_constant_polynomial"
    METHOD_NAME = "Piecewise fit with constant and polynomial"
