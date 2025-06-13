# SPDX-License-Identifier: MIT
from importlib.metadata import PackageNotFoundError, metadata, version

try:
    __version__ = version(__name__)
    _info = metadata(__name__)
    __project__, __author__ = _info["name"], _info["author-email"]
    del _info
except PackageNotFoundError:
    # package is not installed
    __version__ = "<unknown>"
    __project__ = __name__
    __author__ = "<unknown>"
