#!/bin/bash

is_root="$(whoami)"
if [[ $is_root =~ "root" ]]; then
    SUDO=""
else
    SUDO="sudo"
fi

# Required for CI
if [[ $1 == "--yes" ]]; then
    FORCE_APT_INSTALL="-y"
fi

# STM32
$SUDO apt-get install $FORCE_APT_INSTALL gcc-arm-none-eabi stlink-tools

# CAN
$SUDO apt-get install $FORCE_APT_INSTALL can-utils

# Cyphal
pip install -U nunavut
$SUDO apt-get install $FORCE_APT_INSTALL jq python3-scipy
python3 -m pip install --upgrade pip
python3 -m pip install cython pycyphal yakut
