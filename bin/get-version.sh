#!/usr/bin/env bash

set -e

version=$(grep "__version__ = " weasel/about.py)
version=${version/__version__ = }
version=${version/\'/}
version=${version/\'/}
version=${version/\"/}
version=${version/\"/}

echo $version
