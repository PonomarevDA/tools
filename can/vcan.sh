#!/bin/bash
[ "$UID" -eq 0 ] || exec sudo bash "$0" "$@"
script_name=`basename "$0"`

print_help() {
    echo "usage: $script_name [-h] port"
}

if [ "$1" = "--help" ]; then
    print_help
    exit 0
elif [ $# -ne 1 ]; then
    print_help
    echo "$script_name: error: the following arguments are required: port"
    exit 0
fi

modprobe vcan
ip link add dev $1 type vcan
ip link set up $1
