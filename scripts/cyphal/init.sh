#!/bin/bash
# https://github.com/PonomarevDA/tools/blob/main/cyphal/init.sh
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

# Constants
SCRIPT_NAME=$(basename $BASH_SOURCE)
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
REPOSITORY_PATH="$(dirname "$SCRIPT_DIR")"
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Parameters
interface=slcan0
node_id=127
slcan_or_vcan="slcan"

HELP="Usage: $SCRIPT_NAME [--help] [OPTIONS].

The utility automates a few things:
1. It creates CAN interface if it is not exist yet (virtual of based on SLCAN)
2. Configure Yakut environment variables
3. Compile DSDL if they are not compiled yet

Options:
  -h, --help                    Show this help message and exit.
  -i, --interface INTERFACE     Specify custom interface. By default it attach it to $interface.
  -n, --node-id NODE_ID         Specify custom node id. By default $node_id.
  -v, --virtual-can             Specify custom node id. By default $node_id."


function log_error() {
    lineno=($(caller))
    printf "$RED$SCRIPT_NAME ERROR on line ${lineno}: $1!$NC\n"
}

function log_warn() {
    lineno=($(caller))
    printf "$YELLOW$SCRIPT_NAME WARN on line ${lineno}: $1.$NC\n"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
        echo "$HELP"
        [[ "${BASH_SOURCE[0]}" -ef "$0" ]] && exit 0 || return 0
        ;;

        -i|--interface)
        interface=$2
        shift
        ;;

        -n|--node-id)
        node_id=$2
        shift
        ;;

        -v|--virtual-can)
        slcan_or_vcan="vcan"
        ;;

        *)
        log_error "Unknown option: $1"
        echo "$HELP"
        [[ "${BASH_SOURCE[0]}" -ef "$0" ]] && exit 0 || return 1
        ;;
    esac
    shift
done

if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
    log_error "you should source this script, not execute it"
    exit 1
fi

echo "$SCRIPT_NAME config:
- interface=$interface
- node_id=$node_id
- $slcan_or_vcan"

# 1. Create SLCAN based on CAN sniffer
if [[ -z $(ifconfig | grep $interface) ]]; then
    if [[ $slcan_or_vcan == "slcan" ]]; then
        $REPOSITORY_PATH/socketcan.sh -i $interface
    elif [[ $slcan_or_vcan == "vcan" ]]; then
        $REPOSITORY_PATH/socketcan.sh -i $interface -v
    fi
    if [ $? -eq 0 ]; then
        step_result_text="has been created"
    else
        step_result_text="has not been created"
    fi
else
    step_result_text="is already exist"
fi
if [[ $step_result_text == "has not been created" ]]; then
    log_error "1. Interface $interface $step_result_text."
    return 1
else
    echo "1. Interface $interface $step_result_text."
fi


# 2. Configure Cyphal environment variables if they are not already configured
if [ -z ${UAVCAN__CAN__IFACE+x} ]; then
    export UAVCAN__CAN__IFACE="socketcan:$interface"
fi
if [ -z ${UAVCAN__CAN__MTU+x} ]; then
    export UAVCAN__CAN__MTU='8'
fi
if [ -z ${UAVCAN__NODE__ID+x} ]; then
    export UAVCAN__NODE__ID="$node_id"
fi
if [ -z ${CYPHAL_PATH+x} ]; then
    export CYPHAL_PATH="$HOME/.cyphal/zubax_dsdl:$HOME/.cyphal/public_regulated_data_types:$HOME/.cyphal/ds015"
fi
echo "2. Yakut environment variables:
    export UAVCAN__CAN__IFACE=$UAVCAN__CAN__IFACE
    export UAVCAN__CAN__MTU=$UAVCAN__CAN__MTU
    export UAVCAN__NODE__ID=$UAVCAN__NODE__ID
    export CYPHAL_PATH=$CYPHAL_PATH"
