import pytest

from weasel import _util
from weasel._util import validate_spacy_version


def mock_version(package: str) -> str:
    return "3.4.2"


@pytest.mark.parametrize(
    "specifier,should_exit",
    [
        ("3.4.2", False),
        (">=3.4.1", False),
        (">=3.0.1", False),
        (">3.0", False),
        (">3.4", False),
        ("!=3.4.2", True),
        ("3.5.0", True),
    ],
)
def test_spacy(monkeypatch, specifier: str, should_exit: bool):
    monkeypatch.setattr(_util, "version", mock_version)

    if should_exit:
        with pytest.raises(SystemExit):
            validate_spacy_version(dict(spacy_version=specifier))

    else:
        validate_spacy_version(dict(spacy_version=specifier))
