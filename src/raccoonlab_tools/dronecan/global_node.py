#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import sys
import time
import dronecan
from typing import List, Optional, Callable
from raccoonlab_tools.common.device_manager import DeviceManager

class DronecanNode:
    node = None
    def __init__(self, node_id: int = 100) -> None:
        if DronecanNode.node is None:
            transport = DeviceManager.get_device_port()
            if transport.startswith("slcan"):
                dronecan_transport = f'{transport}'
            elif transport.startswith("/dev/") or transport.startswith("COM"):
                dronecan_transport = f'slcan:{transport}'
            else:
                print(f"Unsupported interface {transport}")
                sys.exit(1)

            DronecanNode.node = dronecan.make_node(dronecan_transport,
                                                   node_id=node_id,
                                                   bitrate=1000000,
                                                   baudrate=1000000)
        self.msg = None

    def sub_once(self,
                 data_type,
                 msg_filter : Optional[Callable] = None,
                 timeout_sec=1.5) -> Optional[dronecan.node.TransferEvent]:
        """
        Subscribes to the given topic and wait for first message.

        A simple usage example:
        msg = node.sub_once(dronecan.uavcan.protocol.NodeStatus)

        You can specify a filter to ignore undesirible message, for example:
        crct_filter = lambda msg : msg.message.circuit_id == 500
        msg = node.sub_once(dronecan.uavcan.equipment.power.CircuitStatus, msg_filter=crct_filter)

        By default the functions wait for 1.5 seconds. You can override the timeout:
        msg = node.sub_once(dronecan.uavcan.protocol.NodeStatus, timeout_sec=2.0)
        """
        assert isinstance(msg_filter, Callable) or msg_filter is None
        assert isinstance(timeout_sec, float)
        self.msg = None
        handler = DronecanNode.node.add_handler(data_type, self._callback)

        end_time_sec = time.time() + timeout_sec
        while time.time() < end_time_sec:
            DronecanNode.node.spin(0.005)
            if self.msg is not None and (msg_filter is None or msg_filter(self.msg)):
                break
            else:
                self.msg = None

        handler.remove()
        return self.msg

    def sub_multiple(self,
                     data_type,
                     number_of_messages : int,
                     msg_filter : Optional[Callable] = None,
                     timeout_sec : float=1.5) -> List[Optional[dronecan.node.TransferEvent]]:
        """
        Subscribes to the given topic and wait for given number_of_messages messages.
        """
        assert isinstance(msg_filter, Callable) or msg_filter is None
        assert isinstance(timeout_sec, float)
        list_of_messages = [None] * number_of_messages
        handler = DronecanNode.node.add_handler(data_type, self._callback)

        for idx in range(number_of_messages):
            end_time_sec = time.time() + timeout_sec
            while time.time() < end_time_sec:
                DronecanNode.node.spin(0.005)
                if self.msg is not None and (msg_filter is None or msg_filter(self.msg)):
                    list_of_messages[idx] = self.msg
                    break

        handler.remove()
        return list_of_messages

    def publish(self, msg):
        DronecanNode.node.broadcast(msg)

    def _callback(self, event):
        self.msg = event
        self.msg.timestamp = time.time()
