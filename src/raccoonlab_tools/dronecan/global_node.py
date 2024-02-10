#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import time
import dronecan
from raccoonlab_tools.common.device_manager import DeviceManager

class DronecanNode:
    node = None
    def __init__(self) -> None:
        if DronecanNode.node is None:
            can_transport = f'slcan:{DeviceManager.get_sniffer()}'
            DronecanNode.node = dronecan.make_node(can_transport,
                                                   node_id=100,
                                                   bitrate=1000000,
                                                   baudrate=1000000)
        self.msg = None

    def sub_once(self, data_type, timeout_sec=1.0) -> tuple:
        self.msg = None
        handler = DronecanNode.node.add_handler(data_type, self._callback)
        for _ in range(int(timeout_sec * 1000)):
            DronecanNode.node.spin(0.001)
            if self.msg is not None:
                break
        handler.remove()
        return self.msg

    def _callback(self, event):
        self.msg = event
        self.msg.timestamp = time.time()
