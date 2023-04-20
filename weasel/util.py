# code copied from spacy/util.py

import importlib
import logging
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import warnings
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Any, Generator, Iterator, List, Optional, Tuple, Union

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from .compat import is_windows
from .errors import Errors, Warnings

# We cannot use catalogue in all cases
# because it relies on the zipp library
try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:
    from catalogue._importlib_metadata import PackageNotFoundError  # noqa
    from catalogue._importlib_metadata import version  # noqa

logger = logging.getLogger("spacy")
logger_stream_handler = logging.StreamHandler()
logger_stream_handler.setFormatter(
    logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
)
logger.addHandler(logger_stream_handler)


class ENV_VARS:
    CONFIG_OVERRIDES = "SPACY_CONFIG_OVERRIDES"
    PROJECT_USE_GIT_VERSION = "SPACY_PROJECT_USE_GIT_VERSION"


class SimpleFrozenDict(dict):
    """Simplified implementation of a frozen dict, mainly used as default
    function or method argument (for arguments that should default to empty
    dictionary). Will raise an error if user or spaCy attempts to add to dict.
    """

    def __init__(self, *args, error: str = Errors.E095, **kwargs) -> None:
        """Initialize the frozen dict. Can be initialized with pre-defined
        values.

        error (str): The error message when user tries to assign to dict.
        """
        super().__init__(*args, **kwargs)
        self.error = error

    def __setitem__(self, key, value):
        raise NotImplementedError(self.error)

    def pop(self, key, default=None):
        raise NotImplementedError(self.error)

    def update(self, other):
        raise NotImplementedError(self.error)


class SimpleFrozenList(list):
    """Wrapper class around a list that lets us raise custom errors if certain
    attributes/methods are accessed. Mostly used for properties like
    Language.pipeline that return an immutable list (and that we don't want to
    convert to a tuple to not break too much backwards compatibility). If a user
    accidentally calls nlp.pipeline.append(), we can raise a more helpful error.
    """

    def __init__(self, *args, error: str = Errors.E927) -> None:
        """Initialize the frozen list.

        error (str): The error message when user tries to mutate the list.
        """
        self.error = error
        super().__init__(*args)

    def append(self, *args, **kwargs):
        raise NotImplementedError(self.error)

    def clear(self, *args, **kwargs):
        raise NotImplementedError(self.error)

    def extend(self, *args, **kwargs):
        raise NotImplementedError(self.error)

    def insert(self, *args, **kwargs):
        raise NotImplementedError(self.error)

    def pop(self, *args, **kwargs):
        raise NotImplementedError(self.error)

    def remove(self, *args, **kwargs):
        raise NotImplementedError(self.error)

    def reverse(self, *args, **kwargs):
        raise NotImplementedError(self.error)

    def sort(self, *args, **kwargs):
        raise NotImplementedError(self.error)


def ensure_path(path: Any) -> Any:
    """Ensure string is converted to a Path.

    path (Any): Anything. If string, it's converted to Path.
    RETURNS: Path or original argument.
    """
    if isinstance(path, str):
        return Path(path)
    else:
        return path


def is_compatible_version(
    version: str, constraint: str, prereleases: bool = True
) -> Optional[bool]:
    """Check if a version (e.g. "2.0.0") is compatible given a version
    constraint (e.g. ">=1.9.0,<2.2.1"). If the constraint is a specific version,
    it's interpreted as =={version}.

    version (str): The version to check.
    constraint (str): The constraint string.
    prereleases (bool): Whether to allow prereleases. If set to False,
        prerelease versions will be considered incompatible.
    RETURNS (bool / None): Whether the version is compatible, or None if the
        version or constraint are invalid.
    """
    # Handle cases where exact version is provided as constraint
    if constraint[0].isdigit():
        constraint = f"=={constraint}"
    try:
        spec = SpecifierSet(constraint)
        version = Version(version)  # type: ignore[assignment]
    except (InvalidSpecifier, InvalidVersion):
        return None
    spec.prereleases = prereleases
    return version in spec


def get_minor_version(version: str) -> Optional[str]:
    """Get the major + minor version (without patch or prerelease identifiers).

    version (str): The version.
    RETURNS (str): The major + minor version or None if version is invalid.
    """
    try:
        v = Version(version)
    except (TypeError, InvalidVersion):
        return None
    return f"{v.major}.{v.minor}"


def is_minor_version_match(version_a: str, version_b: str) -> bool:
    """Compare two versions and check if they match in major and minor, without
    patch or prerelease identifiers. Used internally for compatibility checks
    that should be insensitive to patch releases.

    version_a (str): The first version
    version_b (str): The second version.
    RETURNS (bool): Whether the versions match.
    """
    a = get_minor_version(version_a)
    b = get_minor_version(version_b)
    return a is not None and b is not None and a == b


def split_command(command: str) -> List[str]:
    """Split a string command using shlex. Handles platform compatibility.

    command (str) : The command to split
    RETURNS (List[str]): The split command.
    """
    return shlex.split(command, posix=not is_windows)


def join_command(command: List[str]) -> str:
    """Join a command using shlex. shlex.join is only available for Python 3.8+,
    so we're using a workaround here.

    command (List[str]): The command to join.
    RETURNS (str): The joined command
    """
    return " ".join(shlex.quote(cmd) for cmd in command)


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
            message += "\n\nProcess log (stdout and stderr):\n\n"
            message += ret.stdout
        error = subprocess.SubprocessError(message)
        error.ret = ret  # type: ignore[attr-defined]
        error.command = cmd_str  # type: ignore[attr-defined]
        raise error
    elif ret.returncode != 0:
        sys.exit(ret.returncode)
    return ret


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


@contextmanager
def make_tempdir() -> Generator[Path, None, None]:
    """Execute a block in a temporary directory and remove the directory and
    its contents at the end of the with block.

    YIELDS (Path): The path of the temp directory.
    """
    d = Path(tempfile.mkdtemp())
    yield d

    # On Windows, git clones use read-only files, which cause permission errors
    # when being deleted. This forcibly fixes permissions.
    def force_remove(rmfunc, path, ex):
        os.chmod(path, stat.S_IWRITE)
        rmfunc(path)

    try:
        shutil.rmtree(str(d), onerror=force_remove)
    except PermissionError as e:
        warnings.warn(Warnings.W091.format(dir=d, msg=e))


def is_cwd(path: Union[Path, str]) -> bool:
    """Check whether a path is the current working directory.

    path (Union[Path, str]): The directory path.
    RETURNS (bool): Whether the path is the current working directory.
    """
    return str(Path(path).resolve()).lower() == str(Path.cwd().resolve()).lower()


def import_file(name: str, loc: Union[str, Path]) -> ModuleType:
    """Import module from a file. Used to load models from a directory.

    name (str): Name of module to load.
    loc (str / Path): Path to the file.
    RETURNS: The loaded module.
    """
    spec = importlib.util.spec_from_file_location(name, str(loc))
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def check_bool_env_var(env_var: str) -> bool:
    """Convert the value of an environment variable to a boolean. Add special
    check for "0" (falsy) and consider everything else truthy, except unset.

    env_var (str): The name of the environment variable to check.
    RETURNS (bool): Its boolean value.
    """
    value = os.environ.get(env_var, False)
    if value == "0":
        return False
    return bool(value)


def read_package_version(package: str) -> Optional[str]:
    try:
        return version(package)
    except PackageNotFoundError:
        return None


def get_spacy_version_and_commit() -> Tuple[Optional[str], Optional[str]]:

    spacy_version = read_package_version("spacy")

    if spacy_version is not None:
        # Since the version is not None, the package is installed
        from spacy.git_info import GIT_VERSION as SPACY_GIT_VERSION  # noqa

        spacy_commit = SPACY_GIT_VERSION
    else:
        spacy_commit = None

    return spacy_version, spacy_commit
