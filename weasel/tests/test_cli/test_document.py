import os
from pathlib import Path

import pytest
import srsly
from typer.testing import CliRunner

from weasel.__main__ import app

runner = CliRunner()

project_files = [
    "tests/assets/project_files/ner_demo/project.yml",
    "tests/assets/project_files/ner_drugs/project.yml",
]


@pytest.fixture(scope="function", params=project_files)
def project_yaml_file(request, tmp_path_factory):
    config_contents = Path(request.param).read_text()
    local_file = Path("project.yml")
    local_file.write_text(config_contents)
    yield request.param
    local_file.unlink()


def test_create_docs(project_yaml_file):
    result = runner.invoke(app, ["document"])
    conf_data = srsly.read_yaml(project_yaml_file)
    assert result.exit_code == 0
    assert conf_data["title"] in result.stdout


def test_raise_error_no_config():
    result = runner.invoke(app, ["document"])
    assert result.exit_code == 1
