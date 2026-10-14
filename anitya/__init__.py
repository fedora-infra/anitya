# -*- coding: utf-8 -*-

"""Module anitya"""

from importlib import metadata

__api_version__ = "1.2"
try:
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
