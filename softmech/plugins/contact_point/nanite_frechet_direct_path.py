"""Nanite-style contact point detection: Frechet direct path."""

from ._nanite_base import NanitePOCBase

NAME = "Frechet Direct Path (Nanite)"
DESCRIPTION = "Estimate contact point using Frechet distance to direct path"
VERSION = "1.0.0"
DOI = ""


class ContactPointDetector(NanitePOCBase):
    METHOD = "frechet_direct_path"
    METHOD_NAME = "Frechet distance to direct path"
