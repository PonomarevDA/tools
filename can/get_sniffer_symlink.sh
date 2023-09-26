#!/bin/bash
# Brief: Get a sniffer symlink
# Usage: source get_sniffer_symlinks.sh
# Output environment variables:
# - DEV_PATH_SYMLINK

SCRIPT_NAME=$(basename $BASH_SOURCE)
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color
if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
    printf "$RED$SCRIPT_NAME ERROR on line ${LINENO}: you should source this script, not execute it!$NC\n"
    exit 1
fi

KNOWN_SNIFFERS=(
    "ID_MODEL_ID=374b|ID_VENDOR_ID=0483" # RaccoonLab programmer-sniffer
    "ID_MODEL_ID=60c7|ID_VENDOR_ID=1d50" # Zubax Babel-Babel
)

EXPECTED_DEV_PATH="/dev/ttyACM*"
EXPECTED_SYMLINK_PATH="/dev/serial/by-id/"
for dev_path in $EXPECTED_DEV_PATH; do
    [ -e "$dev_path" ] || continue
    for sniffer in ${KNOWN_SNIFFERS[@]}; do
        is_sniffer=$(udevadm info $dev_path | grep -E "($sniffer)" -wc || true)
        if [ "$is_sniffer" == 2 ]; then
            DEV_PATH_SYMLINK=$(find -L $EXPECTED_SYMLINK_PATH -samefile $dev_path)
            echo "Sniffer found: $DEV_PATH_SYMLINK"
            break
        fi
    done
done

if [ -z "$DEV_PATH_SYMLINK" ]; then
    printf "$RED$SCRIPT_NAME Can't find a sniffer!$NC\n"
    # Note: We must use return in a sourced script, otherwise it must be exit!
    [[ "${BASH_SOURCE[0]}" -ef "$0" ]] && exit 0 || return
fi
