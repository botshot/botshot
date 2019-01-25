from pkgutil import extend_path
from botshot.version import __version__

# FIXME: Is this needed?s
__path__ = extend_path(__path__, __name__)
