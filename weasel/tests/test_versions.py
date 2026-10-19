import pytest

from weasel.util.versions import is_compatible_version


@pytest.mark.parametrize("prereleases,expected", [(True, True), (False, False)])
def test_is_compatible_version(prereleases, expected):
    assert is_compatible_version("1.5a1", ">=1,<2", prereleases) is expected
