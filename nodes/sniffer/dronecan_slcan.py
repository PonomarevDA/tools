#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import dronecan
from dronecan import uavcan
node = dronecan.make_node('slcan:/dev/ttyACM0', bitrate=1000000, baudrate=1000000)

def handle_node_status(data):
    print(data.message)

node.add_handler(uavcan.protocol.NodeStatus, handle_node_status)
node.spin(1.5)
