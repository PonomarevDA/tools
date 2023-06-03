#!/bin/bash
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color
print_help() {
    script_name=`basename "$0"`
    echo "This script creates virtual CAN port using slcan. Usage:"
    echo "./$script_name --help                 Call this help."
    echo "./$script_name                        Use automatic device path search and default virtual CAN name."
    echo "./$script_name /dev/ttyACMx           Use user device path and default virtual CAN name."
    echo "./$script_name /dev/ttyACMx slcan0    Use user device path and specify virtual CAN name."
}

if [ "$1" = "--help" ]; then
    print_help
    exit 0
fi

# 1. Set tty settings
echo "SLCAN creator settings:"
if [ $# -ge 1 ]; then
    DEV_PATH=$1
    echo "- DEV_PATH:" $DEV_PATH "(user specified)"
else
    SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
    source $SCRIPT_DIR/get_sniffer_symlink.sh
    DEV_PATH=$DEV_PATH_SYMLINK
    echo "- DEV_PATH:" $DEV_PATH "(auto)"
fi
if [ $# -ge 2 ]; then
    INTERFACE_NAME=$2
    echo "- INTERFACE_NAME:" $INTERFACE_NAME "(user specified)"
else
    INTERFACE_NAME=slcan0
    echo "- INTERFACE_NAME:" $INTERFACE_NAME "(auto)"
fi
if [ -z $DEV_PATH ]; then
    printf "$RED$0 ERROR on line ${LINENO}: Can't find expected tty device.$NC\n"
    exit 1
fi
if [ ! -c "$DEV_PATH" ]; then
    printf "$RED$0 ERROR on line ${LINENO}: specified character device path is not exist.$NC\n"
    exit 1
fi
if [[ $(ifconfig | grep $INTERFACE_NAME) ]]; then
    printf "$YELLOW$0 WARNING on line ${LINENO}: specified interface already exist, skip.$NC\n"
    exit 0
fi

# 2. Run daemon slcand from can-utils - link serial interface with a virtual CAN device
# It will get name slcan name base
#   -o              option means open command
#   -s8             option means 1000 Kbit/s CAN bitrate
#   -t hw           option means UART flow control
#   -S $BAUD_RATE   option means uart baud rate
#   $DEV_PATH       position argument means port name
# sudo slcand -o -s8 -t hw -S $BAUD_RATE $DEV_PATH
sudo slcand -o -c -f -s8 -t hw -S 1000000 $DEV_PATH

sudo ip link set up $INTERFACE_NAME

# Setup SocketCAN queue discipline type
# By default it uses pfifo_fast with queue size 10.
# This queue blocks an application when queue is full.
# So, we use pfifo_head_drop. This queueing discipline drops the earliest enqueued
# packet in the case of queue overflow. 
# More about queueing disciplines:
# https://rtime.felk.cvut.cz/can/socketcan-qdisc-final.pdf
sudo tc qdisc add dev $INTERFACE_NAME root handle 1: pfifo_head_drop limit 1000
