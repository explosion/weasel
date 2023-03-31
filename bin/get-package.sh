#!/usr/bin/env bash

set -e

version=$(grep "__title__ = " weasel/about.py)
version=${version/__title__ = }
version=${version/\'/}
version=${version/\'/}
version=${version/\"/}
version=${version/\"/}

echo $version
