from pathlib import Path

import pytest
import srsly
from typer.testing import CliRunner

from weasel._util import app, get_git_version


def has_git():
    try:
        get_git_version()
        return True
    except RuntimeError:
        return False


SAMPLE_PROJECT = {
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

SAMPLE_PROJECT_TEXT = srsly.yaml_dumps(SAMPLE_PROJECT)


@pytest.fixture
def project_dir(tmp_path: Path):
    path = tmp_path / "project"
    path.mkdir()
    (path / "project.yml").write_text(SAMPLE_PROJECT_TEXT)
    yield path


def test_project_document(project_dir: Path):
    readme_path = project_dir / "README.md"
    assert not readme_path.exists(), "README already exists"
    result = CliRunner().invoke(
        app, ["document", str(project_dir), "-o", str(readme_path)]
    )
    assert result.exit_code == 0
    assert readme_path.is_file()
    text = readme_path.read_text("utf-8")
    assert SAMPLE_PROJECT["description"] in text


def test_project_assets(project_dir: Path):
    asset_dir = project_dir / "assets"
    assert not asset_dir.exists(), "Assets dir is already present"
    result = CliRunner().invoke(app, ["assets", str(project_dir)])
    assert result.exit_code == 0
    assert (asset_dir / "weasel-readme.md").is_file(), "Assets not downloaded"
    # check that extras work
    result = CliRunner().invoke(app, ["assets", "--extra", str(project_dir)])
    assert result.exit_code == 0
    assert (asset_dir / "pyproject.toml").is_file(), "Extras not downloaded"


def test_project_run(project_dir: Path):
    # make sure dry run works
    test_file = project_dir / "abc.txt"
    result = CliRunner().invoke(app, ["run", "--dry", "create", str(project_dir)])
    assert result.exit_code == 0
    assert not test_file.is_file()
    result = CliRunner().invoke(app, ["run", "create", str(project_dir)])
    assert result.exit_code == 0
    assert test_file.is_file()
    result = CliRunner().invoke(app, ["run", "ok", str(project_dir)])
    assert result.exit_code == 0
    assert "okokok" in result.stdout


@pytest.mark.skipif(not has_git(), reason="git not installed")
@pytest.mark.parametrize(
    "options",
    [
        "",
        # "--sparse",
        "--branch v3",
        "--repo https://github.com/explosion/projects --branch v3",
    ],
)
def test_project_clone(tmp_path: Path, options: str):

    out = tmp_path / "project_clone"
    target = "benchmarks/ner_conll03"
    if not options:
        options = []
    else:
        options = options.split()
    result = CliRunner().invoke(app, ["clone", target, *options, str(out)])
    assert result.exit_code == 0
    assert (out / "README.md").is_file()


def test_project_push_pull(tmp_path: Path, project_dir: Path):
    proj = dict(SAMPLE_PROJECT)
    remote = "xyz"

    remote_dir = tmp_path / "remote"
    remote_dir.mkdir()

    proj["remotes"] = {remote: str(remote_dir)}
    proj_text = srsly.yaml_dumps(proj)
    (project_dir / "project.yml").write_text(proj_text)

    test_file = project_dir / "abc.txt"
    result = CliRunner().invoke(app, ["run", "create", str(project_dir)])
    assert result.exit_code == 0
    assert test_file.is_file()
    result = CliRunner().invoke(app, ["push", remote, str(project_dir)])
    assert result.exit_code == 0
    result = CliRunner().invoke(app, ["run", "clean", str(project_dir)])
    assert result.exit_code == 0
    assert not test_file.exists()
    result = CliRunner().invoke(app, ["pull", remote, str(project_dir)])
    assert result.exit_code == 0
    assert test_file.is_file()