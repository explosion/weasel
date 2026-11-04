import hashlib
import os
import site
import tarfile
import urllib.parse
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Union

from wasabi import msg

from ..errors import Errors
from ..util import check_spacy_env_vars, download_file, ensure_pathy, get_checksum
from ..util import get_hash, make_tempdir, upload_file

if TYPE_CHECKING:
    from cloudpathlib import CloudPath


def is_within_directory(directory: "os.PathLike[str] | str", target: str) -> bool:
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    # commonpath compares whole path components, so a sibling like "/root2"
    # isn't treated as inside "/root"
    try:
        common = os.path.commonpath([abs_directory, abs_target])
    except ValueError:
        # Paths on different drives (Windows)
        return False
    return common == abs_directory


def safe_extract(tar: tarfile.TarFile, path: "os.PathLike[str] | str") -> None:
    """Extract a tar file pulled from a remote, refusing anything that could
    write outside of `path` (CVE-2007-4559, directory traversal).
    """
    members = tar.getmembers()
    for member in members:
        if not is_within_directory(path, os.path.join(path, member.name)):
            raise ValueError(Errors.E801)
    if hasattr(tarfile, "data_filter"):
        # Python 3.12+, and the 3.8.17 / 3.9.17 / 3.10.12 / 3.11.4 security
        # backports. The "data" filter rejects links pointing outside the
        # destination (checked against the real filesystem as members are
        # extracted, so chained links are covered), device files, and
        # unsafe permission bits.
        tar.extractall(path, filter="data")
    else:
        # Without the extraction filters a symlink or hard link member can
        # point outside the destination and a later member can write through
        # it. Lexical checks on link targets can be defeated by chaining
        # links, so links (and special files) are refused outright. Outputs
        # that legitimately contain symlinks can only be pulled on a Python
        # that has the extraction filters.
        for member in members:
            if not (member.isfile() or member.isdir()):
                raise ValueError(Errors.E802.format(name=member.name))
        tar.extractall(path)


class RemoteStorage:
    """Push and pull outputs to and from a remote file storage.

    Remotes can be anything that `smart_open` can support: AWS, GCS, file system,
    ssh, etc.
    """

    def __init__(self, project_root: Path, url: str, *, compression="gz"):
        self.root = project_root
        self.url = ensure_pathy(url)
        self.compression = compression

    def push(
        self, path: Path, command_hash: str, content_hash: str
    ) -> Union["CloudPath", Path]:
        """Compress a file or directory within a project and upload it to a remote
        storage. If an object exists at the full URL, nothing is done.

        Within the remote storage, files are addressed by their project path
        (url encoded) and two user-supplied hashes, representing their creation
        context and their file contents. If the URL already exists, the data is
        not uploaded. Paths are archived and compressed prior to upload.
        """
        loc = self.root / path
        if not loc.exists():
            raise IOError(f"Cannot push {loc}: does not exist.")
        url = self.make_url(path, command_hash, content_hash)
        if url.exists():
            return url
        tmp: Path
        with make_tempdir() as tmp:
            tar_loc = tmp / self.encode_name(str(path))
            mode_string = f"w:{self.compression}" if self.compression else "w"
            with tarfile.open(tar_loc, mode=mode_string) as tar_file:  # type: ignore[call-overload]
                tar_file.add(str(loc), arcname=str(path))
            upload_file(tar_loc, url)
        return url

    def pull(
        self,
        path: Path,
        *,
        command_hash: Optional[str] = None,
        content_hash: Optional[str] = None,
    ) -> Optional[Union["CloudPath", Path]]:
        """Retrieve a file from the remote cache. If the file already exists,
        nothing is done.

        If the command_hash and/or content_hash are specified, only matching
        results are returned. If no results are available, an error is raised.
        """
        dest = self.root / path
        if dest.exists():
            return None
        url = self.find(path, command_hash=command_hash, content_hash=content_hash)
        if url is None:
            return url
        else:
            # Make sure the destination exists
            if not dest.parent.exists():
                dest.parent.mkdir(parents=True)
            tmp: Path
            with make_tempdir() as tmp:
                tar_loc = tmp / url.parts[-1]
                download_file(url, tar_loc)
                mode_string = f"r:{self.compression}" if self.compression else "r"
                with tarfile.open(tar_loc, mode=mode_string) as tar_file:  # type: ignore[call-overload]
                    # This requires that the path is added correctly, relative
                    # to root. This is how we set things up in push()
                    safe_extract(tar_file, self.root)
        return url

    def find(
        self,
        path: Path,
        *,
        command_hash: Optional[str] = None,
        content_hash: Optional[str] = None,
    ) -> Optional[Union["CloudPath", Path]]:
        """Find the best matching version of a file within the storage,
        or `None` if no match can be found. If both the creation and content hash
        are specified, only exact matches will be returned. Otherwise, the most
        recent matching file is preferred.
        """
        name = self.encode_name(str(path))
        urls = []
        if command_hash is not None and content_hash is not None:
            url = self.url / name / command_hash / content_hash
            urls = [url] if url.exists() else []
        elif command_hash is not None:
            if (self.url / name / command_hash).exists():
                urls = list((self.url / name / command_hash).iterdir())
        else:
            if (self.url / name).exists():
                for sub_dir in (self.url / name).iterdir():
                    urls.extend(sub_dir.iterdir())
                if content_hash is not None:
                    urls = [url for url in urls if url.parts[-1] == content_hash]
        if len(urls) >= 2:
            try:
                urls.sort(key=lambda x: x.stat().st_mtime)
            except Exception:
                msg.warn(
                    "Unable to sort remote files by last modified. The file(s) "
                    "pulled from the cache may not be the most recent."
                )
        return urls[-1] if urls else None

    def make_url(
        self, path: Path, command_hash: str, content_hash: str
    ) -> Union["CloudPath", Path]:
        """Construct a URL from a subpath, a creation hash and a content hash."""
        return self.url / self.encode_name(str(path)) / command_hash / content_hash

    def encode_name(self, name: str) -> str:
        """Encode a subpath into a URL-safe name."""
        return urllib.parse.quote_plus(name)


def get_content_hash(loc: Path) -> str:
    return get_checksum(loc)


def get_command_hash(
    site_hash: str, env_hash: str, deps: List[Path], cmd: List[str]
) -> str:
    """Create a hash representing the execution of a command. This includes the
    currently installed packages, whatever environment variables have been marked
    as relevant, and the command.
    """
    check_spacy_env_vars()
    dep_checksums = [get_checksum(dep) for dep in sorted(deps)]
    hashes = [site_hash, env_hash] + dep_checksums
    hashes.extend(cmd)
    creation_bytes = "".join(hashes).encode("utf8")
    return hashlib.md5(creation_bytes).hexdigest()


def get_site_hash():
    """Hash the current Python environment's site-packages contents, including
    the name and version of the libraries. The list we're hashing is what
    `pip freeze` would output.
    """
    site_dirs = site.getsitepackages()
    if site.ENABLE_USER_SITE:
        site_dirs.append(site.getusersitepackages())
    packages = set()
    for site_dir in site_dirs:
        site_path = Path(site_dir)
        if not site_path.is_dir():
            continue
        for subpath in site_path.iterdir():
            if subpath.parts[-1].endswith("dist-info"):
                packages.add(subpath.parts[-1].replace(".dist-info", ""))
    package_bytes = "".join(sorted(packages)).encode("utf8")
    return hashlib.md5(package_bytes).hexdigest()


def get_env_hash(env: Dict[str, str]) -> str:
    """Construct a hash of the environment variables that will be passed into
    the commands.

    Values in the env dict may be references to the current os.environ, using
    the syntax $ENV_VAR to mean os.environ[ENV_VAR]
    """
    env_vars = {}
    for key, value in env.items():
        if value.startswith("$"):
            env_vars[key] = os.environ.get(value[1:], "")
        else:
            env_vars[key] = value
    return get_hash(env_vars)
