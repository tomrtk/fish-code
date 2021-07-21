# pragma: no cover
# noqa: D104
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("nina")
except PackageNotFoundError:  # pragma: no cover
    # package is not installed
    pass
