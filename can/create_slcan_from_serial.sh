#!/bin/bash
SCRIPT_NAME=$(basename $BASH_SOURCE)
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color
function print_help() {
    script_name=`basename "$0"`
    echo "This script creates virtual CAN port using slcan. Usage:"
    echo "./$script_name --help                 Call this help."
    echo "./$script_name                        Use automatic device path search and default virtual CAN name."
    echo "./$script_name /dev/ttyACMx           Use user device path and default virtual CAN name."
    echo "./$script_name /dev/ttyACMx slcan0    Use user device path and specify virtual CAN name."
}

function create_slcan() {
    sudo slcand -o -c -f -s8 -t hw -S 1000000 $dev_path $INTERFACE_NAME
    sleep 1 # without sleep next commands may fail with 'Cannot find device "slcan0"'
    sudo ip link set up $INTERFACE_NAME
    sudo tc qdisc add dev $INTERFACE_NAME root handle 1: pfifo_head_drop limit 1000
}

if [ "$1" = "--help" ]; then
    print_help
    exit 0
fi

# 1. Set tty settings
echo "SLCAN creator settings:"
if [ $# -ge 1 ]; then
    dev_path=$1
    echo "- dev_path:" $dev_path "(user specified)"
else
    SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
    source $SCRIPT_DIR/get_sniffer_symlink.sh
    dev_path=$DEV_PATH_SYMLINK
    echo "- dev_path:" $dev_path "(auto)"
fi
if [ $# -ge 2 ]; then
    INTERFACE_NAME=$2
    echo "- INTERFACE_NAME:" $INTERFACE_NAME "(user specified)"
else
    INTERFACE_NAME=slcan0
    echo "- INTERFACE_NAME:" $INTERFACE_NAME "(auto)"
fi
if [ -z $dev_path ]; then
    printf "$RED$SCRIPT_NAME ERROR on line ${LINENO}: Can't find expected tty device.$NC\n"
    exit 1
fi
if [ ! -c "$dev_path" ]; then
    printf "$RED$SCRIPT_NAME ERROR on line ${LINENO}: specified character device path $dev_path is not exist.$NC\n"
    exit 1
fi
if [[ $(ifconfig | grep $INTERFACE_NAME) ]]; then
    printf "$SCRIPT_NAME INFO on line ${LINENO}: specified interface already exist, skip.\n"
    exit 0
fi

create_slcan

if [[ -z $(ifconfig | grep $INTERFACE_NAME) ]]; then
    printf "$RED$SCRIPT_NAME ERROR on line ${LINENO}: Interface '$INTERFACE_NAME' has not been successfully created.$NC\n"
    # Note: We must use return in a sourced script, otherwise it must be exit!
    [[ "${BASH_SOURCE[0]}" -ef "$0" ]] && exit 0 || return
fi
