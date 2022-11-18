import pytest
from typer.testing import CliRunner

from weasel.cli import app

runner = CliRunner()


@pytest.mark.parametrize("cmd", [None, "--help"])
def test_show_help(cmd):
    """Basic test to confirm help text appears"""
    result = runner.invoke(app, [cmd] if cmd else None)
    print(result.stdout)
    assert "https://github.com/explosion/weasel" in result.stdout


@pytest.fixture(scope="session")
def project_dir(tmp_path_factory):
    # a working directory for the session
    base = tmp_path_factory.mktemp("project")
    return base / "project"


@pytest.fixture(scope="session")
def remote_url(tmp_path_factory):
    # a "remote" for testing
    base = tmp_path_factory.mktemp("remote")
    return base / "remote"


def test_clone(project_dir):
    """Cloning shouldn't fail"""
    result = runner.invoke(app, ["clone", "tutorials/ner_drugs", str(project_dir)])

    print(result.stdout)
    assert result.exit_code == 0
    assert (project_dir / "project.yml").exists()


def test_assets(project_dir):
    result = runner.invoke(app, ["assets", str(project_dir)])

    print(result.stdout)
    assert result.exit_code == 0
    assert (project_dir / "assets/drugs_patterns.jsonl").exists()


def test_run(project_dir):
    result = runner.invoke(app, ["run", "preprocess", str(project_dir)])

    print(result.stdout)
    assert result.exit_code == 0
    assert (project_dir / "corpus/drugs_eval.spacy").exists()


def test_push(project_dir, remote_url):
    # append remote to the file
    with open(project_dir / "project.yml", "a") as project_file:
        project_file.write(f"\nremotes:\n    default: {remote_url}\n")

    result = runner.invoke(app, ["push", "default", str(project_dir)])
    print(result.stdout)
    assert result.exit_code == 0


def test_pull(project_dir):
    # delete a file, and make sure pull restores it
    (project_dir / "corpus/drugs_eval.spacy").unlink()

    result = runner.invoke(app, ["pull", "default", str(project_dir)])
    print(result.stdout)
    assert result.exit_code == 0
    assert (project_dir / "corpus/drugs_eval.spacy").exists()
