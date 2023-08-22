#!/bin/bash
# Brief: Get RaccoonLab sniffer symlink
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

EXPECTED_VID=0483
EXPECTED_PID=374b
EXPECTED_DEV_PATH="/dev/ttyACM*"
EXPECTED_SYMLINK_PATH="/dev/serial/by-id/"

for dev_path in $EXPECTED_DEV_PATH; do
    [ -e "$dev_path" ] || continue
    check_vid_and_pid=$(udevadm info $dev_path |
                        grep -E "(ID_MODEL_ID=$EXPECTED_PID|ID_VENDOR_ID=$EXPECTED_VID)" -wc)
    if [ "$check_vid_and_pid" == 2 ]; then
        DEV_PATH=$dev_path
        DEV_PATH_SYMLINK=$(find -L $EXPECTED_SYMLINK_PATH -samefile $DEV_PATH)
        break
    fi
done

if [ -z "$DEV_PATH_SYMLINK" ]; then
    printf "$RED$SCRIPT_NAME Can't find RaccoonLab sniffer!$NC\n"
    # Note: We must use return in a sourced script, otherwise it must be exit!
    [[ "${BASH_SOURCE[0]}" -ef "$0" ]] && exit 0 || return
fi
