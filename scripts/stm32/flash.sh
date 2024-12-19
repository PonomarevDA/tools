#!/bin/bash
BINARY_FILE=$1
SCRIPT_NAME=$(basename $BASH_SOURCE)

RED='\033[0;31m'
NC='\033[0m'
if [ -z "$BINARY_FILE" ]; then
    echo -e "${RED}$SCRIPT_NAME error on line $LINENO: expected an argument!${NC}"
    exit
elif [ ! -f "$BINARY_FILE" ]; then
    echo -e "${RED}$SCRIPT_NAME error on line $LINENO: specified file $BINARY_FILE is not exist!${NC}"
    exit
elif [[ ! $BINARY_FILE == *.bin ]]; then
    echo -e "${RED}$SCRIPT_NAME error on line $LINENO: speficied file must have .bin extension!${NC}"
    exit
fi

# check version of chip based on the binary file name
# /home/user/Documents/work/mini_v2_node/build/release/node_v3_dronecan_2024.12.18_v1.2.5_cea7821d.bin
# get the last part of the file name, remove the extension
FILE_NAME=$(basename $BINARY_FILE)
NODE_VERSION=$(echo $FILE_NAME | cut -d '_' -f 2)

check_version() {
    vesion=$1
    corresponding_version=""
    if [[ $vesion == *"STM32F1xx"* ]]; then
        corresponding_version="v2"
    elif [[ $vesion == *"STM32G0Bx"* ]]; then
        corresponding_version="v3"
    else
        corresponding_version="unknown"
    fi
    if [[ $corresponding_version == $NODE_VERSION ]]; then
        echo 0
    else
        echo 1
    fi
}

for attempt in {1..25}; do
    echo ""
    echo "Attempt $attempt. Trying to load the firmware..."
    echo -en "\007"

    output=$(st-info --probe)

    is_programmer_not_found=$(echo "$output" | grep "Found 0 stlink programmers")
    if [ ! -z "$is_programmer_not_found" ]; then
        echo "stlink programmer not found. Please connect it to your USB port!"
        sleep 2
        continue
    fi

    is_device_not_found=$(echo "$output" | grep "unknown device")
    if [ ! -z "$is_device_not_found" ]; then
        echo "STM32 not found. Please connect it to the stlink programmer!"
        sleep 2
        continue
    fi

    # stm32f103 has a wrong flash size. It says 64 KBytes, but it is actually 128 KBytes!
    # Medium-density for old versions of st-link, MD for the newer versions of st-link
    is_stm32f103=$(echo "$output" | grep "F1xx Medium-density\|STM32F1xx_MD")
    if [ ! -z "$is_stm32f103" ]; then
        EXPLICIT_FLASH_SIZE="--flash=0x00020000"
    fi

    # get stm32 version from the output
    dev_type=$(echo "$output" | awk 'END{print $2}')
    # Check if the dev_type is not "unknown"
    if [ "$dev_type" != "unknown" ]; then
        # Apply the pattern to get the chip name like F1xx or G0Bx
        chip_name=$(echo "$dev_type" | awk -F '_' '{print $1}')
    else
        # Keep it as "unknown"
        chip_name=$dev_type
    fi

    is_chip_type_supported=$(check_version $chip_name)
    if [ $is_chip_type_supported -eq 0 ]; then
        echo "Chip type $chip_name is supported"
    else
        echo "Chip type $chip_name is not supported. Please, connect appropriate node!"
        sleep 2
        continue
    fi

    output=$(st-flash $EXPLICIT_FLASH_SIZE --reset write $BINARY_FILE 0x8000000 | tee /dev/tty)
    compare_res=$(echo "$output" | grep "pages written")
    if [ -z "$compare_res" ]; then
        sleep 2
    else
        echo Done
        for attempt in {1..15}; do
            sleep 0.1
            echo -en "\007"
        done
        exit
    fi
done

for attempt in {1..15}; do
    sleep 0.1
    echo -en "\007"
done
