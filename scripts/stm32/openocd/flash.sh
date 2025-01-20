#!/bin/bash

target="None"
offset=0x08000000
filename=$1
interface=$2
echo "Filename arg: $filename"
prnt_path=$(dirname $(dirname "$BASH_SOURCE"))

# check f interface was passed
if [ -z "$interface" ]; then
    if [ -f "/proc/device-tree/model" ]; then
        model=$(cat /proc/device-tree/model)
        echo "$model"
        if [[ $model == *"Raspberry Pi 5"* ]]; then
            interface="raspberrypi5-gpiod"
        elif [[ $model == *"Raspberry Pi 4"* ]]; then
            interface="raspberrypi4-native"
        elif [[ $model == *"Raspberry Pi 2"* ]]; then
            interface="raspberrypi2-native"
        else
            echo "raspberrypi-native"
        fi
    else
        interface="stlink"               
    fi
    echo "Using $interface"     
fi
# check if interface is stlink, then flash via st-flash
if [ "$interface" == "stlink" ]; then
    ./${prnt_path}/flash.sh $filename
    exit
fi

check_chip(){
    # Run OpenOCD and capture the output
    output=$(openocd -c "source [find interface/${interface}.cfg]
                        swd newdap chip cpu -enable
                        dap create chip.dap -chain-position chip.cpu
                        target create chip.cpu cortex_m -dap chip.dap

                        init
                        dap info
                        shutdown
                        ")

    # Extract the processor name using grep and awk
    processor_name=$(echo "$output" | awk '/chip.cpu/ {print}' | awk 'NR == 1 {print $4}')
    echo "output: $output"
    # Print the processor name
    echo "Detected Processor: $processor_name"

    # Optionally, detect STM32 family based on the processor name
    case "$processor_name" in
        "Cortex-M0+")
            echo "Detected STM32 Family: STM32G0"
            target="stm32g0x"
            ;;
        "Cortex-M3")
            echo "Detected STM32 Family: STM32F103"
            target="stm32f1x"
            ;;
        *)
            echo "Unknown Processor or Family"
            exit 1
            ;;
    esac

}

check_chip
echo "$target"
flash_size_str=""
if [ "$target" == "stm32f1x" ]; then
    flash_size_str="set FLASH_SIZE 0x00020000"
fi

echo $(openocd -c "
source [find interface/${interface}.cfg]
set CHIPNAME ${target}
source [find target/${target}.cfg]

reset_config  srst_nogate
init
targets
reset halt

${flash_size_str}
${target} mass_erase 0
flash write_image erase $filename $offset
flash verify_image $filename $offset
reset run
exit
")
