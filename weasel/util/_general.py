import sys 
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
import shlex

from ._errors import Warnings
from ._compat import is_windows


Arg = typer.Argument
Opt = typer.Option


logger = logging.getLogger("weasel")
logger_stream_handler = logging.StreamHandler()
logger_stream_handler.setFormatter(
    logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
)
logger.addHandler(logger_stream_handler)


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
