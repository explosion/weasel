import io
import re
import sys
import tarfile
import warnings
from pathlib import Path

import pytest

from weasel.cli.remote_storage import get_site_hash, is_within_directory, safe_extract


def _add_file(tar: tarfile.TarFile, name: str, data: bytes = b"data") -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))


def _add_link(tar: tarfile.TarFile, name: str, target: str, kind: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.type = kind
    info.linkname = target
    tar.addfile(info)


def _make_tar(tmp_path: Path, build) -> Path:
    loc = tmp_path / "archive.tar"
    with tarfile.open(loc, "w") as tar:
        build(tar)
    return loc


@pytest.fixture
def dirs(tmp_path: Path):
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    return root, outside


@pytest.fixture(params=["filter", "fallback"])
def extract_mode(request, monkeypatch):
    """Run each test with the tarfile extraction filters available, and again
    as on a Python without them (< 3.8.17 / 3.9.17 / 3.10.12 / 3.11.4)."""
    if request.param == "filter":
        if not hasattr(tarfile, "data_filter"):
            pytest.skip("tarfile extraction filters not available")
    else:
        monkeypatch.delattr(tarfile, "data_filter", raising=False)
        # 3.12/3.13 warn about extractall() without a filter; the real
        # fallback only runs on Pythons that have no filters to warn about
        warnings.filterwarnings("ignore", category=DeprecationWarning)
    return request.param


def test_is_within_directory_sibling_prefix(tmp_path: Path):
    root = tmp_path / "root"
    assert is_within_directory(root, str(root / "a" / "b"))
    assert not is_within_directory(root, str(tmp_path / "root2" / "x"))
    assert not is_within_directory(root, str(root / ".." / "root2"))


@pytest.mark.usefixtures("extract_mode")
def test_safe_extract_regular_files(tmp_path, dirs):
    root, _ = dirs

    def build(tar):
        info = tarfile.TarInfo("out")
        info.type = tarfile.DIRTYPE
        info.mode = 0o755
        tar.addfile(info)
        _add_file(tar, "out/a.txt", b"hello")

    with tarfile.open(_make_tar(tmp_path, build)) as tar:
        safe_extract(tar, root)
    assert (root / "out" / "a.txt").read_bytes() == b"hello"


@pytest.mark.parametrize("name", ["../root2/evil", "/tmp/evil-weasel-abs"])
@pytest.mark.usefixtures("extract_mode")
def test_safe_extract_rejects_traversal_names(tmp_path, dirs, name):
    root, _ = dirs
    loc = _make_tar(tmp_path, lambda tar: _add_file(tar, name))
    with tarfile.open(loc) as tar:
        with pytest.raises(ValueError, match="unsafe path traversal"):
            safe_extract(tar, root)
    assert not (tmp_path / "root2").exists()


@pytest.mark.skipif(sys.platform == "win32", reason="symlinks need privileges")
@pytest.mark.usefixtures("extract_mode")
def test_safe_extract_rejects_symlink_escape(tmp_path, dirs):
    root, outside = dirs

    def build(tar):
        _add_link(tar, "link", str(outside), tarfile.SYMTYPE)
        _add_file(tar, "link/evil", b"pwned")

    with tarfile.open(_make_tar(tmp_path, build)) as tar:
        # FilterError (with the filters) is a subclass of TarError; the
        # fallback raises ValueError
        with pytest.raises((ValueError, tarfile.TarError)):
            safe_extract(tar, root)
    assert not (outside / "evil").exists()


@pytest.mark.skipif(sys.platform == "win32", reason="symlinks need privileges")
@pytest.mark.usefixtures("extract_mode")
def test_safe_extract_rejects_chained_symlink_escape(tmp_path, dirs):
    root, outside = dirs

    # "d" -> "." looks harmless, and "d/up" -> ".." looks like it stays in
    # root lexically, but resolves to root's parent once "d" exists
    def build(tar):
        _add_link(tar, "d", ".", tarfile.SYMTYPE)
        _add_link(tar, "d/up", "..", tarfile.SYMTYPE)
        _add_file(tar, f"d/up/{outside.name}/evil", b"pwned")

    with tarfile.open(_make_tar(tmp_path, build)) as tar:
        with pytest.raises((ValueError, tarfile.TarError)):
            safe_extract(tar, root)
    assert not (outside / "evil").exists()


@pytest.mark.usefixtures("extract_mode")
def test_safe_extract_rejects_hardlink_escape(tmp_path, dirs):
    root, outside = dirs
    target = outside / "victim.txt"
    target.write_bytes(b"original")

    def build(tar):
        _add_link(tar, "hl", str(target), tarfile.LNKTYPE)

    with tarfile.open(_make_tar(tmp_path, build)) as tar:
        with pytest.raises((ValueError, tarfile.TarError)):
            safe_extract(tar, root)
    assert not (root / "hl").exists()
    assert target.read_bytes() == b"original"


def test_safe_extract_fallback_refuses_internal_symlink(tmp_path, dirs, monkeypatch):
    root, _ = dirs
    monkeypatch.delattr(tarfile, "data_filter", raising=False)

    def build(tar):
        _add_file(tar, "real.txt")
        _add_link(tar, "alias", "real.txt", tarfile.SYMTYPE)

    with tarfile.open(_make_tar(tmp_path, build)) as tar:
        with pytest.raises(ValueError, match="link or special file"):
            safe_extract(tar, root)


def test_get_site_hash():
    assert re.fullmatch(r"[0-9a-f]{32}", get_site_hash())
