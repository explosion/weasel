#!/usr/bin/env python

import os
import subprocess
from pathlib import Path
import re


# Include the git version in the build (adapted from NumPy)
# Copyright (c) 2005-2020, NumPy Developers.
# BSD 3-Clause license, see licenses/3rd_party_licenses.txt
def write_git_info_py(filename="weasel/git_info.py"):
    def _minimal_ext_cmd(cmd):
        # construct minimal environment
        env = {}
        for k in ["SYSTEMROOT", "PATH", "HOME"]:
            v = os.environ.get(k)
            if v is not None:
                env[k] = v
        # LANGUAGE is used on win32
        env["LANGUAGE"] = "C"
        env["LANG"] = "C"
        env["LC_ALL"] = "C"
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, env=env)
        return out

    git_version = "Unknown"
    filepath = Path(filename)

    if Path(".git").exists():
        try:
            out = _minimal_ext_cmd(["git", "rev-parse", "--short", "HEAD"])
            git_version = out.strip().decode("ascii")
        except Exception:
            pass
    elif filepath.exists():
        # must be a source distribution, use existing version file
        try:
            a = open(filename, "r")
            lines = a.readlines()
            git_version = lines[-1].split('"')[1]
        except Exception:
            pass
        finally:
            a.close()

    text = f"""# THIS FILE IS GENERATED FROM WEASEL SETUP.PY
#
GIT_VERSION = "{git_version}"
"""

    filepath.write_text(text)


def write_version_py():
    """A utility for automatic version extration from setup.py."""

    config = Path("setup.cfg").read_text()
    path = Path("weasel/_version.py")

    match = re.search(r"(?<=version = ).+", config)
    version = match.groupdict()["version"]

    path.write_text(f'__version__ = "{version}"\n')


if __name__ == "__main__":
    from setuptools import find_packages, setup

    write_version_py()
    write_git_info_py()

    setup(packages=find_packages())
