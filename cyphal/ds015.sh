#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
REPOSITORY_PATH="$(dirname "$SCRIPT_DIR")"

UAVCAN_DSDL_PATH=$REPOSITORY_PATH/public_regulated_data_types/uavcan
UDRAL_DSDL_PATH=$REPOSITORY_PATH/public_regulated_data_types/reg
DS015_DSDL_PATH=$REPOSITORY_PATH/ds015

REG_DATA_TYPE_PATH="$UAVCAN_DSDL_PATH $UDRAL_DSDL_PATH $DS015_DSDL_PATH"
export YAKUT_COMPILE_OUTPUT="build/nunavut_out"

source $SCRIPT_DIR/init.sh
