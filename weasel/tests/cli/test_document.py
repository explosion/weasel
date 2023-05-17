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
def project_yaml_file(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
):
    full_path = BASE_PATH / Path(request.param)
    config_contents = full_path.read_text()

    test_dir = tmp_path_factory.mktemp("project")
    path = test_dir / "project.yml"
    path.write_text(config_contents)
    return path


def test_create_docs(project_yaml_file: Path):
    result = runner.invoke(app, ["document", str(project_yaml_file.parent)])
    conf_data = srsly.read_yaml(project_yaml_file)
    assert result.exit_code == 0
    assert conf_data["title"] in result.stdout


def test_raise_error_no_config():
    result = runner.invoke(app, ["document"])
    assert result.exit_code == 1
