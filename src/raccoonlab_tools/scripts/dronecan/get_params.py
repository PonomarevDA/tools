#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
import sys
import dronecan
from raccoonlab_tools.dronecan.utils import ParametersInterface, NodeFinder
from raccoonlab_tools.common.device_manager import DeviceManager

def main():
    all_sniffers = DeviceManager().get_all_online_sniffers()
    if len(all_sniffers) == 0:
        print("[ERROR] CAN-sniffer has not been automatically found.")
        sys.exit(1)
    can_transport = f'slcan:{all_sniffers[0].port}'

    node = dronecan.make_node(can_transport, node_id=100, bitrate=1000000, baudrate=1000000)
    target_node_id = NodeFinder(node).find_online_node()
    params_interface = ParametersInterface(node=node, target_node_id=target_node_id)
    all_params = params_interface.get_all()
    for param in all_params:
        print(param)

if __name__ =="__main__":
    main()
