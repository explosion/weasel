from pathlib import Path

import pytest
import srsly
from typer.testing import CliRunner

from weasel import app

BASE_PATH = Path(__file__).parent.parent.resolve()

runner = CliRunner()

project_files = [
    "assets/project_files/ner_demo/project.yml",
    "assets/project_files/ner_drugs/project.yml",
]


@pytest.fixture(scope="function", params=project_files)
def project_yaml_file(request, tmp_path_factory):
    full_path = BASE_PATH / Path(request.param)
    config_contents = full_path.read_text()
    local_file = Path("project.yml")
    local_file.write_text(config_contents)
    yield full_path
    local_file.unlink()


def test_create_docs(project_yaml_file):
    result = runner.invoke(app, ["document"])
    conf_data = srsly.read_yaml(project_yaml_file)
    assert result.exit_code == 0
    assert conf_data["title"] in result.stdout


def test_raise_error_no_config():
    result = runner.invoke(app, ["document"])
    assert result.exit_code == 1
