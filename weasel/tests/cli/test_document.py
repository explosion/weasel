from pathlib import Path
from typing import Any, Dict

import pytest
import srsly
from typer.testing import CliRunner

from weasel import app

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
