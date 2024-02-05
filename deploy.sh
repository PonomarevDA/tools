#!/bin/bash

print_help() {
   echo "usage: deploy.sh [OPTION]

This script deploys the package to either TestPyPI (by default) or PyPI:
- https://test.pypi.org/project/raccoonlab-tools/
- https://pypi.org/project/raccoonlab-tools/

Options:
  --pypi    Upload to PyPI instead of TestPyPI."
}

# Parse args
if [ ! "${BASH_SOURCE[0]}" -ef "$0" ]; then
    echo "You should execute this script, not source it!"
    return
elif [[ $1 == "--pypi" ]]; then
    echo Deploying to PyPi...
    REPOSITORY=""   # empty means PyPi
elif [ ! -z $1 ]; then
    print_help
    exit
else
    echo Deploying to TestPyPI...
    REPOSITORY="--repository testpypi"
fi

# Main
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR
rm -rf dist/
rm -rf src/raccoonlab_tools.egg-info
python3 -m build
python3 -m twine upload $REPOSITORY dist/*
