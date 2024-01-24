#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import dronecan
import time
import pytest

class DronecanNode:
    node = None
    def __init__(self) -> None:
        if DronecanNode.node is None:
            DronecanNode.node = dronecan.make_node(f'slcan:/dev/ttyACM0', bitrate=1000000, baudrate=1000000)

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

class TestNodeStatus:
    """
    All nodes are required to publish NodeStatus periodically.
    """
    def test_existance(self):
        """
        NodeStatus should appear with health=0 and vssc=2.
        """
        node = DronecanNode()
        msg = node.sub_once(dronecan.uavcan.protocol.NodeStatus)
        assert msg is not None
        assert msg.message.health == 0
        assert msg.message.vendor_specific_status_code == 2

    def test_publishing_period(self):
        """
        NodeStatus publishing period should be exactly 500 ms.
        1. Wait for 5 NodeStatus.
        2. Peiod check: All 4 periods must be 0.5 +- 0.05 seconds
        3. Watchdog check: The last uptime must be 2 or 3 seconds after the first one
        """
        node = DronecanNode()

        msgs = []
        timestamps = []
        for _ in range(5):
            msg = node.sub_once(dronecan.uavcan.protocol.NodeStatus)
            msgs.append(msg)
            timestamps.append(msg.timestamp)

        periods = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps) - 1)]
        for number in periods:
            assert pytest.approx(number, abs=0.05) == 0.5

        uptame_elapsed = msgs[-1].message.uptime_sec - msgs[0].message.uptime_sec
        assert uptame_elapsed == 2 or uptame_elapsed == 3
