#!/bin/bash
script_name=`basename "$0"`

print_help() {
    echo "usage: $script_name [-h] <port>"
    echo "example: $script_name slcan0"
}

if [ "$1" = "--help" ]; then
    print_help
    [[ "${BASH_SOURCE[0]}" -ef "$0" ]] && exit 0 || return
elif [ $# -ne 1 ]; then
    print_help
    echo "$script_name: error: the following arguments are required: port"
    [[ "${BASH_SOURCE[0]}" -ef "$0" ]] && exit 0 || return
fi

[ "$UID" -eq 0 ] || exec sudo bash "$0" "$@"

modprobe vcan
ip link add dev $1 type vcan
ip link set up $1
