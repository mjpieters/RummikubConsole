# SPDX-License-Identifier: MIT
try:
    from importlib_resources import version, PackageNotFoundError
except ImportError:
    from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
    __version__ = "<unknown>"
