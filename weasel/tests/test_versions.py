import pytest

from weasel.util.versions import (
    get_minor_version,
    is_compatible_version,
    is_minor_version_match,
)


@pytest.mark.parametrize(
    "version,constraint,expected",
    [
        ("1.0.0", ">=0.9", True),
        ("1.0.0", "1.0.0", True),
        ("1.0.0", ">=2.0", False),
        ("1.0.0", "not a constraint", None),
        ("not a version", ">=1.0", None),
        ("1.0.0", "", None),
        ("", ">=1.0", None),
    ],
)
def test_is_compatible_version(version, constraint, expected):
    assert is_compatible_version(version, constraint) is expected


def test_get_minor_version_invalid():
    assert get_minor_version("") is None
    assert get_minor_version("not a version") is None


def test_is_minor_version_match_invalid():
    assert is_minor_version_match("", "1.2.3") is False
    assert is_minor_version_match("1.2.3", "") is False
