import os
import shutil
import stat
import tempfile
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Iterator, Union

from weasel.errors import Warnings


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


def ensure_path(path: Any) -> Any:
    """Ensure string is converted to a Path.

    path (Any): Anything. If string, it's converted to Path.
    RETURNS: Path or original argument.
    """
    if isinstance(path, str):
        return Path(path)
    else:
        return path
