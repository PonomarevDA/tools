#!/bin/bash
SCRIPT_NAME=$(basename $BASH_SOURCE)
OUTPUT_FILE_NAME="git_hash.h"
RED='\033[0;31m'
NC='\033[0m'
print_help() {
    echo "This script generates C header file $OUTPUT_FILE_NAME with GIT_HASH define related to the latest commit."
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

echo "
/// This software is distributed under the terms of the MIT License.
/// Copyright (c) 2022 Dmitry Ponomarev.
/// Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
#pragma once
#define GIT_HASH 0x$(git rev-parse --short=16 HEAD)
" > $1/$OUTPUT_FILE_NAME

echo "INFO: successfully generated: $1/$OUTPUT_FILE_NAME"
