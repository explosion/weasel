from typing import Any, Callable, Optional

import pytest

from weasel import util
from weasel._util import validate_spacy_version


def mock_version(output: Optional[str]) -> Callable[[Any], Optional[str]]:
    def f(package):
        return output

    return f


@pytest.mark.parametrize(
    "version,specifier,should_exit",
    [
        ("3.4.2", "3.4.2", False),
        ("3.4.2", ">=3.4.1", False),
        ("3.4.2", ">=3.0.1", False),
        ("3.4.2", ">3.0", False),
        ("3.4.2", ">3.4", False),
        ("3.4.2", "!=3.4.2", True),
        ("3.4.2", "3.5.0", True),
        (None, "3.4.2", False),
        (None, ">=3.4.1", False),
        (None, ">=3.0.1", False),
        (None, ">3.0", False),
        (None, ">3.4", False),
        (None, "!=3.4.2", False),
        (None, "3.5.0", False),
    ],
)
def test_spacy(monkeypatch, version: Optional[str], specifier: str, should_exit: bool):
    monkeypatch.setattr(util, "version", mock_version(version))

    if should_exit:
        with pytest.raises(SystemExit):
            validate_spacy_version(dict(spacy_version=specifier))

    else:
        validate_spacy_version(dict(spacy_version=specifier))
