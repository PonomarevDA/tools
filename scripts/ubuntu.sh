#!/bin/bash
SCRIPT_NAME=$(basename $BASH_SOURCE)
REPO_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
HELP="usage: $SCRIPT_NAME [-h|--help] [-y|--yes] [--stm32-only] [--cyphal-only] [--cyphal-only].

The scripts intstall dependencies for RaccoonLab tools.

options:
    -y, --yes               Force yes when install with APT. Usefull for CI.
    --cyphal-only           Install only Cyphal dependencies.
    --dronecan-only         Install only DroneCAN dependencies.
    --stm32-only            Install only STM32 dependencies.
    -h, --help              Show this help message and exit.
"

is_root="$(whoami)"
if [[ $is_root =~ "root" ]]; then
    SUDO=""
else
    SUDO="sudo"
fi

# Parse arguments
INSTALL_DRONECAN='y'
INSTALL_CYPHAL='y'
INSTALL_STM32='n'
while [[ $# -gt 0 ]]; do
    case $1 in
        -y|--yes)
        FORCE_APT_INSTALL="-y"
        ;;

        --cyphal-only)
        INSTALL_DRONECAN="n"
        INSTALL_CYPHAL="y"
        INSTALL_STM32="n"
        ;;

        --dronecan-only)
        INSTALL_DRONECAN="y"
        INSTALL_CYPHAL="n"
        INSTALL_STM32="n"
        ;;

        --stm32-only)
        INSTALL_DRONECAN="n"
        INSTALL_CYPHAL="n"
        INSTALL_STM32="y"
        ;;

        -h|--help)
        echo "$HELP"
        [[ "${BASH_SOURCE[0]}" -ef "$0" ]] && exit 0 || return 0
        ;;

        *)
        echo "Unknown option: $1"
        echo "$HELP"
        [[ "${BASH_SOURCE[0]}" -ef "$0" ]] && exit 1 || return 1
        ;;
    esac
    shift
done

# 1. Install common dependency for DroneCAN and Cyphal
$SUDO apt-get install $FORCE_APT_INSTALL net-tools # ifconfig: command not found
$SUDO apt-get install $FORCE_APT_INSTALL can-utils # sudo: slcand: command not found
$SUDO apt-get install $FORCE_APT_INSTALL iproute2 # sudo: ip: command not found, sudo: tc: command not found
python3 -m pip install pyserial python-can pytest

kernel_release=$(uname -r)
if [[ $kernel_release == *azure ]]; then
    $SUDO apt-get install $FORCE_APT_INSTALL linux-modules-extra-$(uname -r)
fi

# 2. Install DroneCAN dependency
if [[ $INSTALL_DRONECAN == 'y' ]]; then
    python3 -m pip install pydronecan 
fi

# 3. Install Cyphal dependency and clone Cyphal DSDL
if [[ $INSTALL_CYPHAL == 'y' ]]; then
    python3 -m pip install yakut pytest pytest-asyncio # cython pycyphal jq
    git clone https://github.com/OpenCyphal/public_regulated_data_types.git ~/.cyphal/public_regulated_data_types
    git clone https://github.com/Zubax/zubax_dsdl.git ~/.cyphal/zubax_dsdl
    git clone -b pr-add-gnss https://github.com/PonomarevDA/ds015.git ~/.cyphal/ds015
fi

# 5. STM32
if [[ $INSTALL_STM32 == 'y' ]]; then
    $SUDO apt-get install $FORCE_APT_INSTALL gcc-arm-none-eabi stlink-tools
fi
