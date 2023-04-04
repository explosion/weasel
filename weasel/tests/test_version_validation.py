import pytest

from weasel._util import validate_spacy_version


@pytest.mark.parametrize(
    "specifier,should_exit",
    [
        ("3.5.1", False),
        (">=3.5.1", False),
        (">=3.5.1", False),
        (">3.0", False),
        (">3.4", False),
        ("!=3.5.1", True),
        ("3.5.0", True),
    ],
)
def test_spacy(specifier: str, should_exit: bool):

    if should_exit:
        with pytest.raises(SystemExit):
            validate_spacy_version(dict(spacy_version=specifier))

    else:
        validate_spacy_version(dict(spacy_version=specifier))
