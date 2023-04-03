#!/usr/bin/env python

from pathlib import Path
import re


def write_version_py():
    """A utility for automatic version extration from setup.py."""

    config = Path("setup.cfg").read_text()
    path = Path("weasel/_version.py")

    match = re.search(r"(?<=version = ).+", config)
    version = match.group()

    path.write_text(f'__version__ = "{version}"\n')


if __name__ == "__main__":
    from setuptools import find_packages, setup

    write_version_py()

    setup(packages=find_packages())
