# import logging
# import os
# import shutil
# import warnings
# import tempfile
# from contextlib import contextmanager
# from typing import List, Mapping, NoReturn, Union, Dict, Any, Set, cast
# from typing import Optional, Iterable, Callable, Tuple, Type
# from typing import Iterator, Pattern, Generator, TYPE_CHECKING
# from pathlib import Path
# from .util._errors import Warnings

# logger = logging.getLogger("weasel")
# logger_stream_handler = logging.StreamHandler()
# logger_stream_handler.setFormatter(
#     logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
# )
# logger.addHandler(logger_stream_handler)


# def ensure_path(path: Any) -> Any:
#     """Ensure string is converted to a Path.

#     path (Any): Anything. If string, it's converted to Path.
#     RETURNS: Path or original argument.
#     """
#     if isinstance(path, str):
#         return Path(path)
#     else:
#         return path


# @contextmanager
# def working_dir(path: Union[str, Path]) -> Iterator[Path]:
#     """Change current working directory and returns to previous on exit.

#     path (str / Path): The directory to navigate to.
#     YIELDS (Path): The absolute path to the current working directory. This
#         should be used if the block needs to perform actions within the working
#         directory, to prevent mismatches with relative paths.
#     """
#     prev_cwd = Path.cwd()
#     current = Path(path).resolve()
#     os.chdir(str(current))
#     try:
#         yield current
#     finally:
#         os.chdir(str(prev_cwd))


# @contextmanager
# def make_tempdir() -> Generator[Path, None, None]:
#     """Execute a block in a temporary directory and remove the directory and
#     its contents at the end of the with block.

#     YIELDS (Path): The path of the temp directory.
#     """
#     d = Path(tempfile.mkdtemp())
#     yield d
#     try:
#         shutil.rmtree(str(d))
#     except PermissionError as e:
#         warnings.warn(Warnings.W091.format(dir=d, msg=e))


# def is_cwd(path: Union[Path, str]) -> bool:
#     """Check whether a path is the current working directory.

#     path (Union[Path, str]): The directory path.
#     RETURNS (bool): Whether the path is the current working directory.
#     """
#     return str(Path(path).resolve()).lower() == str(Path.cwd().resolve()).lower()


# class SimpleFrozenDict(dict):
#     """Simplified implementation of a frozen dict, mainly used as default
#     function or method argument (for arguments that should default to empty
#     dictionary). Will raise an error if user or spaCy attempts to add to dict.
#     """

#     def __init__(self, *args, error: str = Errors.E095, **kwargs) -> None:
#         """Initialize the frozen dict. Can be initialized with pre-defined
#         values.

#         error (str): The error message when user tries to assign to dict.
#         """
#         super().__init__(*args, **kwargs)
#         self.error = error

#     def __setitem__(self, key, value):
#         raise NotImplementedError(self.error)

#     def pop(self, key, default=None):
#         raise NotImplementedError(self.error)

#     def update(self, other):
#         raise NotImplementedError(self.error)


# def parse_config_overrides(
#     args: List[str], env_var: Optional[str] = ENV_VARS.CONFIG_OVERRIDES
# ) -> Dict[str, Any]:
#     """Generate a dictionary of config overrides based on the extra arguments
#     provided on the CLI, e.g. --training.batch_size to override
#     "training.batch_size". Arguments without a "." are considered invalid,
#     since the config only allows top-level sections to exist.

#     env_vars (Optional[str]): Optional environment variable to read from.
#     RETURNS (Dict[str, Any]): The parsed dict, keyed by nested config setting.
#     """
#     env_string = os.environ.get(env_var, "") if env_var else ""
#     env_overrides = _parse_overrides(split_arg_string(env_string))
#     cli_overrides = _parse_overrides(args, is_cli=True)
#     if cli_overrides:
#         keys = [k for k in cli_overrides if k not in env_overrides]
#         logger.debug(f"Config overrides from CLI: {keys}")
#     if env_overrides:
#         logger.debug(f"Config overrides from env variables: {list(env_overrides)}")
#     return {**cli_overrides, **env_overrides}


# def _parse_overrides(args: List[str], is_cli: bool = False) -> Dict[str, Any]:
#     result = {}
#     while args:
#         opt = args.pop(0)
#         err = f"Invalid config override '{opt}'"
#         if opt.startswith("--"):  # new argument
#             orig_opt = opt
#             opt = opt.replace("--", "")
#             if "." not in opt:
#                 if is_cli:
#                     raise NoSuchOption(orig_opt)
#                 else:
#                     msg.fail(f"{err}: can't override top-level sections", exits=1)
#             if "=" in opt:  # we have --opt=value
#                 opt, value = opt.split("=", 1)
#                 opt = opt.replace("-", "_")
#             else:
#                 if not args or args[0].startswith("--"):  # flag with no value
#                     value = "true"
#                 else:
#                     value = args.pop(0)
#             result[opt] = _parse_override(value)
#         else:
#             msg.fail(f"{err}: name should start with --", exits=1)
#     return result
