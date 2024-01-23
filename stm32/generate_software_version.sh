#!/bin/bash
SCRIPT_NAME=$(basename $BASH_SOURCE)
OUTPUT_FILE_NAME="git_software_version.h"
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'
print_help() {
    echo "This script generates C header file $OUTPUT_FILE_NAME with application major and minor version defines."
    echo "Usage:   $SCRIPT_NAME <output dir>"
    echo "Example: $SCRIPT_NAME build/src"
}

if [ "$#" -ne 1 ]; then
    print_help
    exit
elif [ ! -d $1 ]; then
    printf "${RED}Error: directory $1 does not exists.$NC\n"
    exit
fi

LAST_TAG=$(git tag | sort -V | tail -1)
IFS='.' read -ra ADDR <<< "$LAST_TAG"
MAJOR_SW_VERSION="${ADDR[0]:1}"
MINOR_SW_VERSION=${ADDR[1]}
PATH_SW_VERSION=${ADDR[2]}
if [ -z $LAST_TAG ]; then
    printf "${YELLOW}Warning: Git Tags are not exist! Use v0.0.0.$NC\n"
    MAJOR_SW_VERSION="0"
    MINOR_SW_VERSION="0"
    PATH_SW_VERSION="0"
elif [[ -z "$MAJOR_SW_VERSION" ]] || [[ -z "$MINOR_SW_VERSION" ]] || [[ -z "$PATH_SW_VERSION" ]]; then
    printf "${RED}Error: Git Tags are broken!$NC\n"
    exit -1
else
    echo Software version is v$MAJOR_SW_VERSION.$MINOR_SW_VERSION.$PATH_SW_VERSION.
fi

echo "
/// This software is distributed under the terms of the MIT License.
/// Copyright (c) 2024 Dmitry Ponomarev.
/// Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
#pragma once
#define APP_VERSION_MAJOR $MAJOR_SW_VERSION
#define APP_VERSION_MINOR $MINOR_SW_VERSION
" > $1/$OUTPUT_FILE_NAME
