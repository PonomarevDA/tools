#!/bin/bash
export CYPHAL_PATH="$HOME/.cyphal/zubax_dsdl:$HOME/.cyphal/public_regulated_data_types/"
export UAVCAN__NODE__ID=127
export UAVCAN__CAN__IFACE="socketcan:slcan0"
export UAVCAN__CAN__BITRATE="1000000 1000000"
export UAVCAN__CAN__MTU=8
