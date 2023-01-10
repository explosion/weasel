import os

import pytest
from typer.testing import CliRunner

from weasel.cli import app
from weasel.cli.run import run_commands
from weasel._util.compat import is_windows
from weasel._util.general import run_command

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
    # TODO point to main
    repo = "https://github.com/koaning/weasel"
    branch = "proposal-layout"
    result = runner.invoke(
        app,
        [
            "clone",
            "--repo",
            repo,
            "--branch",
            branch,
            "weasel/tests/demo_project",
            str(project_dir),
        ],
    )

    print(result.stdout)
    assert result.exit_code == 0
    assert (project_dir / "project.yml").exists()


def test_assets(project_dir):
    result = runner.invoke(app, ["assets", str(project_dir)])

    print(result.stdout)
    assert result.exit_code == 0
    assert (project_dir / "assets/README.md").exists()


def test_run(project_dir):
    result = runner.invoke(app, ["run", "prep", str(project_dir)])

    print(result.stdout)
    assert result.exit_code == 0
    assert (project_dir / "corpus/stuff.txt").exists()


def test_push(project_dir, remote_url):
    # append remote to the file
    with open(project_dir / "project.yml", "a") as project_file:
        project_file.write(f"\nremotes:\n    default: {remote_url}\n")

    result = runner.invoke(app, ["push", "default", str(project_dir)])
    print(result.stdout)
    assert result.exit_code == 0


def test_pull(project_dir):
    # delete a file, and make sure pull restores it
    (project_dir / "corpus/stuff.txt").unlink()

    result = runner.invoke(app, ["pull", "default", str(project_dir)])
    print(result.stdout)
    assert result.exit_code == 0
    assert (project_dir / "corpus/stuff.txt").exists()


def test_shell_quoting(tmp_path):
    # simple quoted shell commands should run on any platform
    # because mkdir is one of the few cross-platform commands,
    # we'll work in a temp dir (pytest global fixture)
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        ret = run_command('mkdir "a b"')
        assert ret.returncode == 0

        # If things are working correctly, "a b"/c and "a b/c" should evaluate
        # to the same directory. If they are working incorrectly, these could
        # be treated differently.

        # the slash here also works as a directory separator on Windows,
        # for these commands at least.
        ret = run_command('mkdir "a b"/c')
        assert ret.returncode == 0
        ls_cmd = "dir" if is_windows else "ls"
        ret = run_command(f'{ls_cmd} "a b/c"')
        assert ret.returncode == 0
        # check outside the commands
        assert os.path.isdir(tmp_path / "a b" / "c")
        # since this is a temp dir, we don't have to delete it explicitly
    finally:
        # restore the original cwd so other tests are unaffected
        os.chdir(cwd)


def test_run_commands(tmp_path):
    # minimal test
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        ls_cmd = "dir" if is_windows else "ls"
        run_commands(["mkdir x", f"{ls_cmd} x"])
        # check outside the commands
        assert os.path.isdir(tmp_path / "x")
    finally:
        # restore the original cwd so other tests are unaffected
        os.chdir(cwd)
