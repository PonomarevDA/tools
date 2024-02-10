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
    DEPLOY_REPOSITORY=""   # empty means PyPi
elif [ ! -z $1 ]; then
    print_help
    exit
else
    echo Deploying to TestPyPI...
    DEPLOY_REPOSITORY="--repository testpypi"
fi

# Main
SCRIPTS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR="$(dirname "$SCRIPTS_DIR")"
cd $ROOT_DIR
rm -rf dist/
rm -rf src/raccoonlab_tools.egg-info
python3 -m build
python3 -m twine upload $DEPLOY_REPOSITORY dist/*
