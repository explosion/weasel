#!/usr/bin/env bash

set -e

version=$(grep "version = " pyproject.toml)
version=${version/version = }
version=${version/\'/}
version=${version/\'/}
version=${version/\"/}
version=${version/\"/}

echo $version
