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


# project tests

SAMPLE_PROJECT = {
    "title": "Sample project",
    "description": "This is a project for testing",
    "assets": [
        {
            "dest": "assets/spacy-readme.md",
            "url": "https://github.com/explosion/spaCy/raw/dec81508d28b47f09a06203c472b37f00db6c869/README.md",
            "checksum": "411b2c89ccf34288fae8ed126bf652f7",
        },
        {
            "dest": "assets/citation.cff",
            "url": "https://github.com/explosion/spaCy/raw/master/CITATION.cff",
            "checksum": "c996bfd80202d480eb2e592369714e5e",
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
    assert (asset_dir / "spacy-readme.md").is_file(), "Assets not downloaded"
    # check that extras work
    result = CliRunner().invoke(app, ["assets", "--extra", str(project_dir)])
    assert result.exit_code == 0
    assert (asset_dir / "citation.cff").is_file(), "Extras not downloaded"


def test_project_run(project_dir: Path):
    # make sure dry run works
    test_file = project_dir / "abc.txt"
    result = CliRunner().invoke(
        app, ["run", "--dry", "create", str(project_dir)]
    )
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
