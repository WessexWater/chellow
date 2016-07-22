from ._version import get_versions
from chellow.views import app

__all__ = [app]

versions = get_versions()
__version__ = versions['version']
del get_versions
