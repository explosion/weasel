#!/usr/bin/env bash

set -e

version=$(grep "name = " pyproject.toml)
version=${version/__title__ = }
version=${version/\'/}
version=${version/\'/}
version=${version/\"/}
version=${version/\"/}

echo $version
