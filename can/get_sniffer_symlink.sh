#!/bin/bash
# Brief: Get a sniffer symlink
# Usage: source get_sniffer_symlinks.sh
# Output environment variables:
# - DEV_PATH
# - DEV_PATH_SYMLINK

SCRIPT_NAME=$(basename $BASH_SOURCE)
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color
if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
    printf "$RED$SCRIPT_NAME ERROR on line ${LINENO}: you should source this script, not execute it!$NC\n"
    exit 1
fi

EXPECTED_DEV_PATH="/dev/ttyACM*"
EXPECTED_SYMLINK_PATH="/dev/serial/by-id/"

# Known sniffers:
RACCOON_LAB_VID=0483
RACCOON_LAB_PID=374b
ZUBAX_BABEL_VID=1d50
ZUBAX_BABEL_PID=60c7


for dev_path in $EXPECTED_DEV_PATH; do
    [ -e "$dev_path" ] || continue
    is_rl_sniffer=$(udevadm info $dev_path | grep -E "(ID_MODEL_ID=$RACCOON_LAB_PID|ID_VENDOR_ID=$RACCOON_LAB_VID)" -wc || true)
    if [ "$is_rl_sniffer" == 2 ]; then
        DEV_PATH=$dev_path
        DEV_PATH_SYMLINK=$(find -L $EXPECTED_SYMLINK_PATH -samefile $DEV_PATH)
        echo "RaccoonLab sniffer has been detected."
        break
    fi

    is_zubax_sniffer=$(udevadm info $dev_path | grep -E "(ID_MODEL_ID=$ZUBAX_BABEL_PID|ID_VENDOR_ID=$ZUBAX_BABEL_VID)" -wc || true)
    if [ "$is_zubax_sniffer" == 2 ]; then
        DEV_PATH=$dev_path
        DEV_PATH_SYMLINK=$(find -L $EXPECTED_SYMLINK_PATH -samefile $DEV_PATH)
        echo "$SCRIPT_NAME: Zubax Babel-Babel has been detected."
        break
    fi
done

if [ -z "$DEV_PATH_SYMLINK" ]; then
    printf "$RED$SCRIPT_NAME Can't find a sniffer!$NC\n"
    # Note: We must use return in a sourced script, otherwise it must be exit!
    [[ "${BASH_SOURCE[0]}" -ef "$0" ]] && exit 0 || return
fi
