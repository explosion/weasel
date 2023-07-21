from pathlib import Path
from typing import Any, Dict

import pytest
import srsly
from typer.testing import CliRunner

from weasel import app
from weasel.cli.document import MARKER_END, MARKER_IGNORE, MARKER_START, MARKER_TAGS

runner = CliRunner()

SAMPLE_PROJECT: Dict[str, Any] = {
    "title": "Sample project",
    "description": "This is a project for testing",
    "assets": [
        {
            "dest": "assets/weasel-readme.md",
            "url": "https://github.com/explosion/weasel/raw/9a3632862b47069d2f9033b773e814d4c4e09c83/README.md",
            "checksum": "65f4c426a9b153b7683738c92d0d20f9",
        },
        {
            "dest": "assets/pyproject.toml",
            "url": "https://github.com/explosion/weasel/raw/9a3632862b47069d2f9033b773e814d4c4e09c83/pyproject.toml",
            "checksum": "1e2da3a3030d6611520952d5322cd94e",
            "extra": True,
        },
    ],
    "commands": [
        {
            "name": "ok",
            "help": "print ok",
            "script": ["python -c \"print('okokok')\""],
        },
        {
            "name": "create",
            "help": "make a file",
            "script": ["touch abc.txt"],
            "outputs": ["abc.txt"],
        },
        {
            "name": "clean",
            "help": "remove test file",
            "script": ["rm abc.txt"],
        },
    ],
}


@pytest.fixture(scope="function")
def project_yaml_file(
    tmp_path_factory: pytest.TempPathFactory,
):
    test_dir = tmp_path_factory.mktemp("project")
    path = test_dir / "project.yml"
    path.write_text(srsly.yaml_dumps(SAMPLE_PROJECT))
    return path


def test_create_docs(project_yaml_file: Path):
    result = runner.invoke(app, ["document", str(project_yaml_file.parent)])
    conf_data = srsly.read_yaml(project_yaml_file)
    assert result.exit_code == 0
    assert conf_data["title"] in result.stdout


def test_raise_error_no_config():
    result = runner.invoke(app, ["document"])
    assert result.exit_code == 1


@pytest.mark.parametrize("marker", MARKER_TAGS)
def test_markers(tmp_path_factory: pytest.TempPathFactory, marker: str):
    """Weasel should be able to handle both 'SPACY PROJECT' and 'WEASEL' markers."""
    project: Dict[str, Any] = {
        "title": "Awesome project",
        "description": "Project using spacy projects and gets migrated to weasel.",
    }
    additional_text = (
        "\n\n## Some additional information\n\nHere is some additional information about this project "
        "that is not autogenerated from the [`project.yml`](project.yml)."
    )

    # Create project file.
    test_dir = tmp_path_factory.mktemp("project")
    path = test_dir / "project.yml"
    path.write_text(srsly.yaml_dumps(project))

    # Store readme with additional information.
    # runner.invoke(app, ["document", str(path.parent), "--output", test_dir / "readme.md"])
    with open(test_dir / "readme.md", "w+", encoding="utf-8") as file:
        readme = runner.invoke(app, ["document", str(path.parent)]).output
        for to_replace in (MARKER_START, MARKER_END, MARKER_IGNORE):
            readme = readme.replace(
                to_replace.format(tag="WEASEL"), to_replace.format(tag=marker)
            )
        file.writelines(readme)
        file.writelines(additional_text)

    # Run `document` again on existing readme file. Ensure additional information is still there.
    runner.invoke(
        app, ["document", str(path.parent), "--output", test_dir / "readme.md"]
    )
    with open(test_dir / "readme.md", "r", encoding="utf-8") as file:
        assert additional_text in "".join(file.readlines())
