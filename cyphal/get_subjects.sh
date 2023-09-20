#!/bin/bash
NODE_ID=$1

registers_string=$(y rl $NODE_ID | tr -d '"' | tr ',' ' ')
registers_string=${registers_string#"|"}
registers_string=${registers_string%"|"}
registers_array=($registers_string)
subjects=()

for register in "${registers_array[@]}"; do
    if [[ $register == uavcan.pub.* ]] && [[ $register == *.id ]]; then
        subject=${register::-3}
        subject=$(echo $subject | cut -c 12-)
        subjects+=($subject)
    fi
done

echo "Publishers: "
for subject in "${subjects[@]}"; do
    echo "- $subject "
done
echo ""
