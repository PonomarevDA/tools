#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023 Dmitry Ponomarev.
import dronecan
from raccoonlab_tools.dronecan.utils import ParametersInterface

def main():
    node = dronecan.make_node('slcan:/dev/ttyACM0', node_id=100, bitrate=1000000, baudrate=1000000)
    params_interface = ParametersInterface(node=node, target_node_id=50)
    all_params = params_interface.get_all()
    for param in all_params:
        print(param)

if __name__ =="__main__":
    main()
