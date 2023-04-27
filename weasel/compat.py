import sys

is_windows = sys.platform.startswith("win")
is_linux = sys.platform.startswith("linux")
is_osx = sys.platform == "darwin"

try:
    from importlib.metadata import version  # noqa
except ImportError:
    from catalogue._importlib_metadata import version  # type: ignore [no-redef]  # noqa
