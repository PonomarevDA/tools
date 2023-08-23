#!/bin/bash
SCRIPT_NAME=$(basename $BASH_SOURCE)
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color
print_help() {
    echo "Usage: source $SCRIPT_NAME"
}

if [ "$1" = "--help" ]; then
    print_help
    # Note: We must use return in a sourced script, otherwise it must be exit!
    [[ "${BASH_SOURCE[0]}" -ef "$0" ]] && exit 0 || return
fi

if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
    printf "$RED$SCRIPT_NAME ERROR on line ${LINENO}: you should source this script, not execute it!$NC\n"
    exit 1
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
REPOSITORY_PATH="$(dirname "$SCRIPT_DIR")"
DEFAULT_PUBLIC_DSDL_PATH="$REPOSITORY_PATH/public_regulated_data_types"
DEFAULT_UAVCAN_DSDL_PATH="$DEFAULT_PUBLIC_DSDL_PATH/uavcan"
DEFAULT_REG_DSDL_PATH="$DEFAULT_PUBLIC_DSDL_PATH/reg"

# 1. Create SLCAN based on CAN sniffer
res=$(ifconfig | grep slcan0)
if [ -z "$res" ]; then
    $REPOSITORY_PATH/can/create_slcan_from_serial.sh
fi

# 2. Configure environment variables if they are not already configured
if [ -z ${REG_DATA_TYPE_PATH+x} ]; then
    REG_DATA_TYPE_PATH="$DEFAULT_UAVCAN_DSDL_PATH $DEFAULT_REG_DSDL_PATH"
fi
if [ -z ${YAKUT_COMPILE_OUTPUT+x} ]; then
    export YAKUT_COMPILE_OUTPUT="$REPOSITORY_PATH/compile_output"
fi
if [ -z ${YAKUT_PATH+x} ]; then
    export YAKUT_PATH="$YAKUT_COMPILE_OUTPUT"
fi
if [ -z ${UAVCAN__CAN__IFACE+x} ]; then
    export UAVCAN__CAN__IFACE='socketcan:slcan0'
fi

export UAVCAN__CAN__MTU=8
export UAVCAN__NODE__ID=127

# 3. Compile DSDL based on public regulated data types
if [ -d $YAKUT_COMPILE_OUTPUT ] && [ "$(ls -A $YAKUT_COMPILE_OUTPUT)" ]; then
    :
else
    dsdl_path_array=($REG_DATA_TYPE_PATH)
    for dsdl_path in "${dsdl_path_array[@]}"; do
        if [ ! -d "$dsdl_path" ]; then
            printf "$YELLOW$SCRIPT_NAME WARN on line ${LINENO}: $dsdl_path does not exist.$NC\n"
        fi
    done

    yakut compile $REG_DATA_TYPE_PATH -O $YAKUT_COMPILE_OUTPUT
fi
