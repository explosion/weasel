import sys

if sys.version_info[:2] >= (3, 8):  # Python 3.8+
    from typing import Literal
else:
    from typing_extensions import Literal  # noqa: F401


is_windows = sys.platform.startswith("win")
is_linux = sys.platform.startswith("linux")
is_osx = sys.platform == "darwin"
