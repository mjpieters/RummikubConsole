# SPDX-License-Identifier: MIT
from importlib.metadata import metadata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from importlib.metadata import PackageNotFoundError, version
else:
    try:  # python 3.8 and older
        from importlib_resources import PackageNotFoundError, version
    except ImportError:
        from importlib.metadata import PackageNotFoundError, version

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
