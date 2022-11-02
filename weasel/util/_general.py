import sys
import hashlib 
import typer
import subprocess
import logging
import os
import shutil
import warnings
import tempfile
from contextlib import contextmanager
from typing import List, Mapping, NoReturn, Union, Dict, Any, Set, cast
from typing import Optional, Iterable, Callable, Tuple, Type
from typing import Iterator, Pattern, Generator, TYPE_CHECKING
from pathlib import Path
from pydantic import BaseModel
import shlex
import srsly
from wasabi import msg

from ._errors import Warnings
from ._compat import is_windows
from ._schema import (
    validate,
    validate_project_version,
    validate_project_commands,
    show_validation_error,
    ProjectConfigSchema,
)
from ..info import PROJECT_FILE, PROJECT_LOCK, COMMAND

from weasel import __version__ as weasel_version 

Arg = typer.Argument
Opt = typer.Option


logger = logging.getLogger("weasel")
logger_stream_handler = logging.StreamHandler()
logger_stream_handler.setFormatter(
    logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
)
logger.addHandler(logger_stream_handler)


class SimpleFrozenDict(dict):
    """Simplified implementation of a frozen dict, mainly used as default
    function or method argument (for arguments that should default to empty
    dictionary). Will raise an error if user or spaCy attempts to add to dict.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the frozen dict. Can be initialized with pre-defined
        values.

        error (str): The error message when user tries to assign to dict.
        """
        super().__init__(*args, **kwargs)
        self.error = "Can't write to frozen dictionary. This is likely an internal error. Are you writing to a default function argument?"

    def __setitem__(self, key, value):
        raise NotImplementedError(self.error)

    def pop(self, key, default=None):
        raise NotImplementedError(self.error)

    def update(self, other):
        raise NotImplementedError(self.error)


def run_command(
    command: Union[str, List[str]],
    *,
    stdin: Optional[Any] = None,
    capture: bool = False,
) -> subprocess.CompletedProcess:
    """Run a command on the command line as a subprocess. If the subprocess
    returns a non-zero exit code, a system exit is performed.

    command (str / List[str]): The command. If provided as a string, the
        string will be split using shlex.split.
    stdin (Optional[Any]): stdin to read from or None.
    capture (bool): Whether to capture the output and errors. If False,
        the stdout and stderr will not be redirected, and if there's an error,
        sys.exit will be called with the return code. You should use capture=False
        when you want to turn over execution to the command, and capture=True
        when you want to run the command more like a function.
    RETURNS (Optional[CompletedProcess]): The process object.
    """
    if isinstance(command, str):
        cmd_list = split_command(command)
        cmd_str = command
    else:
        cmd_list = command
        cmd_str = " ".join(command)
    try:
        ret = subprocess.run(
            cmd_list,
            env=os.environ.copy(),
            input=stdin,
            encoding="utf8",
            check=False,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.STDOUT if capture else None,
        )
    except FileNotFoundError:
        # Indicates the *command* wasn't found, it's an error before the command
        # is run.
        raise FileNotFoundError(
            Errors.E970.format(str_command=cmd_str, tool=cmd_list[0])
        ) from None
    if ret.returncode != 0 and capture:
        message = f"Error running command:\n\n{cmd_str}\n\n"
        message += f"Subprocess exited with status {ret.returncode}"
        if ret.stdout is not None:
            message += f"\n\nProcess log (stdout and stderr):\n\n"
            message += ret.stdout
        error = subprocess.SubprocessError(message)
        error.ret = ret  # type: ignore[attr-defined]
        error.command = cmd_str  # type: ignore[attr-defined]
        raise error
    elif ret.returncode != 0:
        sys.exit(ret.returncode)
    return ret


def split_command(command: str) -> List[str]:
    """Split a string command using shlex. Handles platform compatibility.

    command (str) : The command to split
    RETURNS (List[str]): The split command.
    """
    return shlex.split(command, posix=not is_windows)


def ensure_path(path: Any) -> Any:
    """Ensure string is converted to a Path.

    path (Any): Anything. If string, it's converted to Path.
    RETURNS: Path or original argument.
    """
    if isinstance(path, str):
        return Path(path)
    else:
        return path


@contextmanager
def make_tempdir() -> Generator[Path, None, None]:
    """Execute a block in a temporary directory and remove the directory and
    its contents at the end of the with block.

    YIELDS (Path): The path of the temp directory.
    """
    d = Path(tempfile.mkdtemp())
    yield d
    try:
        shutil.rmtree(str(d))
    except PermissionError as e:
        warnings.warn(Warnings.W091.format(dir=d, msg=e))


def is_subpath_of(parent, child):
    """
    Check whether `child` is a path contained within `parent`.
    """
    # Based on https://stackoverflow.com/a/37095733 .

    # In Python 3.9, the `Path.is_relative_to()` method will supplant this, so
    # we can stop using crusty old os.path functions.
    parent_realpath = os.path.realpath(parent)
    child_realpath = os.path.realpath(child)
    return os.path.commonpath([parent_realpath, child_realpath]) == parent_realpath


@contextmanager
def working_dir(path: Union[str, Path]) -> Iterator[Path]:
    """Change current working directory and returns to previous on exit.

    path (str / Path): The directory to navigate to.
    YIELDS (Path): The absolute path to the current working directory. This
        should be used if the block needs to perform actions within the working
        directory, to prevent mismatches with relative paths.
    """
    prev_cwd = Path.cwd()
    current = Path(path).resolve()
    os.chdir(str(current))
    try:
        yield current
    finally:
        os.chdir(str(prev_cwd))


def load_project_config(
    path: Path, interpolate: bool = True, overrides: Dict[str, Any] = SimpleFrozenDict()
) -> Dict[str, Any]:
    """Load the project.yml file from a directory and validate it. Also make
    sure that all directories defined in the config exist.

    path (Path): The path to the project directory.
    interpolate (bool): Whether to substitute project variables.
    overrides (Dict[str, Any]): Optional config overrides.
    RETURNS (Dict[str, Any]): The loaded project.yml.
    """
    config_path = path / PROJECT_FILE
    if not config_path.exists():
        msg.fail(f"Can't find {PROJECT_FILE}", config_path, exits=1)
    invalid_err = f"Invalid {PROJECT_FILE}. Double-check that the YAML is correct."
    try:
        config = srsly.read_yaml(config_path)
    except ValueError as e:
        msg.fail(invalid_err, e, exits=1)
    errors = validate(ProjectConfigSchema, config)
    if errors:
        msg.fail(invalid_err)
        print("\n".join(errors))
        sys.exit(1)
    validate_project_version(config)
    validate_project_commands(config)
    # Make sure directories defined in config exist
    for subdir in config.get("directories", []):
        dir_path = path / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
    # TODO: double-check interpolation and thinc import here
    # if interpolate:
    #     err = f"{PROJECT_FILE} validation error"
    #     with show_validation_error(title=err, hint_fill=False):
    #         config = substitute_project_variables(config, overrides)
    return config


def get_hash(data, exclude: Iterable[str] = tuple()) -> str:
    """Get the hash for a JSON-serializable object.

    data: The data to hash.
    exclude (Iterable[str]): Top-level keys to exclude if data is a dict.
    RETURNS (str): The hash.
    """
    if isinstance(data, dict):
        data = {k: v for k, v in data.items() if k not in exclude}
    data_str = srsly.json_dumps(data, sort_keys=True).encode("utf8")
    return hashlib.md5(data_str).hexdigest()


def get_checksum(path: Union[Path, str]) -> str:
    """Get the checksum for a file or directory given its file path. If a
    directory path is provided, this uses all files in that directory.

    path (Union[Path, str]): The file or directory path.
    RETURNS (str): The checksum.
    """
    path = Path(path)
    if not (path.is_file() or path.is_dir()):
        msg.fail(f"Can't get checksum for {path}: not a file or directory", exits=1)
    if path.is_file():
        return hashlib.md5(Path(path).read_bytes()).hexdigest()
    else:
        # TODO: this is currently pretty slow
        dir_checksum = hashlib.md5()
        for sub_file in sorted(fp for fp in path.rglob("*") if fp.is_file()):
            dir_checksum.update(sub_file.read_bytes())
        return dir_checksum.hexdigest()


def download_file(src: Union[str, "Pathy"], dest: Path, *, force: bool = False) -> None:
    """Download a file using smart_open.

    url (str): The URL of the file.
    dest (Path): The destination path.
    force (bool): Whether to force download even if file exists.
        If False, the download will be skipped.
    """
    import smart_open

    if dest.exists() and not force:
        return None
    src = str(src)
    with smart_open.open(src, mode="rb", ignore_ext=True) as input_file:
        with dest.open(mode="wb") as output_file:
            shutil.copyfileobj(input_file, output_file)


def ensure_pathy(path):
    """Temporary helper to prevent importing Pathy globally (which can cause
    slow and annoying Google Cloud warning)."""
    from pathy import Pathy  # noqa: F811

    return Pathy(path)


def get_lock_entry(project_dir: Path, command: Dict[str, Any]) -> Dict[str, Any]:
    """Get a lockfile entry for a given command. An entry includes the command,
    the script (command steps) and a list of dependencies and outputs with
    their paths and file hashes, if available. The format is based on the
    dvc.lock files, to keep things consistent.

    project_dir (Path): The current project directory.
    command (Dict[str, Any]): The command, as defined in the project.yml.
    RETURNS (Dict[str, Any]): The lockfile entry.
    """
    deps = get_fileinfo(project_dir, command.get("deps", []))
    outs = get_fileinfo(project_dir, command.get("outputs", []))
    outs_nc = get_fileinfo(project_dir, command.get("outputs_no_cache", []))
    return {
        "cmd": f"{COMMAND} run {command['name']}",
        "script": command["script"],
        "deps": deps,
        "outs": [*outs, *outs_nc],
        "spacy_version": weasel_version,
    }


def get_fileinfo(project_dir: Path, paths: List[str]) -> List[Dict[str, Optional[str]]]:
    """Generate the file information for a list of paths (dependencies, outputs).
    Includes the file path and the file's checksum.

    project_dir (Path): The current project directory.
    paths (List[str]): The file paths.
    RETURNS (List[Dict[str, str]]): The lockfile entry for a file.
    """
    data = []
    for path in paths:
        file_path = project_dir / path
        md5 = get_checksum(file_path) if file_path.exists() else None
        data.append({"path": path, "md5": md5})
    return data
    
    
def update_lockfile(project_dir: Path, command: Dict[str, Any]) -> None:
    """Update the lockfile after running a command. Will create a lockfile if
    it doesn't yet exist and will add an entry for the current command, its
    script and dependencies/outputs.

    project_dir (Path): The current project directory.
    command (Dict[str, Any]): The command, as defined in the project.yml.
    """
    lock_path = project_dir / PROJECT_LOCK
    if not lock_path.exists():
        srsly.write_yaml(lock_path, {})
        data = {}
    else:
        data = srsly.read_yaml(lock_path)
    data[command["name"]] = get_lock_entry(project_dir, command)
    srsly.write_yaml(lock_path, data)
