#!/bin/bash
SCRIPT_NAME=$(basename $BASH_SOURCE)
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
TOOLS_DIR=$SCRIPT_DIR/..
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color
print_help() {
    echo "Usage: $SCRIPT_NAME [PATH_TO_BINARY] [PATH_TO_YAML_FILE_WITH_DRONECAN_PARAMS]"
}

if [ "$1" = "--help" ]; then
    print_help
    # Note: We must use return in a sourced script, otherwise it must me exit!
    [[ "${BASH_SOURCE[0]}" -ef "$0" ]] && exit 0 || return
fi

if [ ! "${BASH_SOURCE[0]}" -ef "$0" ]; then
    printf "$RED$SCRIPT_NAME ERROR on line ${LINENO}: you should execute this script, not source it!$NC\n"
    return
fi

$TOOLS_DIR/stm32/flash.sh $1
$TOOLS_DIR/can/create_slcan_from_serial.sh
$TOOLS_DIR/dronecan/param_setter.py --file-path $2 --write
