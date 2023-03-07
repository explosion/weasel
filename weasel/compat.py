import sys

if sys.version_info[:2] >= (3, 8):  # Python 3.8+
    from typing import Literal
else:
    from typing_extensions import Literal  # noqa: F401