#!/bin/bash
print_help() {
    script_name=`basename "$0"`
    echo "Usage: source $script_name"
}

if [ "$1" = "--help" ]; then
    print_help
    exit 0
fi

if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
    echo "$0 ERROR on line ${LINENO}: you should source this script, not execute it!"
    exit 1
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SRC_PATH="$(dirname "$SCRIPT_DIR")"
REPOSITORY_PATH="$(dirname "$SRC_PATH")"
DEFAULT_PUBLIC_DSDL_PATH="$REPOSITORY_PATH/public_regulated_data_types"
DEFAULT_UAVCAN_DSDL_PATH="$DEFAULT_PUBLIC_DSDL_PATH/uavcan"
DEFAULT_REG_DSDL_PATH="$DEFAULT_PUBLIC_DSDL_PATH/reg"

# 1. Create SLCAN based on CAN sniffer
res=$(ifconfig | grep slcan0)
if [ -z "$res" ]; then
    $SRC_PATH/can/create_slcan_from_serial.sh $CYPHAL_DEV_PATH_SYMLINK
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
            echo "$0 WARN on line ${LINENO}: $dsdl_path does not exist."
        fi
    done

    yakut compile $REG_DATA_TYPE_PATH -O $YAKUT_COMPILE_OUTPUT
fi
