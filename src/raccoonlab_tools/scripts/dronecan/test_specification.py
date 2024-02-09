#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import sys
import time
import os
import subprocess
import dronecan
import pytest

from raccoonlab_tools.common.device_manager import DeviceManager

HEALTH_OK = 0
MODE_OPERATIONAL = 0
VSSC_RACCOONLAB_RELEASE = 2

class DronecanNode:
    node = None
    def __init__(self) -> None:
        if DronecanNode.node is None:
            can_transport = f'slcan:{DeviceManager.find_sniffer_or_exit()}'
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

class TestNodeStatus:
    """
    All nodes are required to publish NodeStatus periodically.
    """
    @staticmethod
    def test_health():
        node = DronecanNode()
        msg = node.sub_once(dronecan.uavcan.protocol.NodeStatus)  # pylint: disable=no-member
        assert msg.message.health == HEALTH_OK

    @staticmethod
    def test_mode():
        node = DronecanNode()
        msg = node.sub_once(dronecan.uavcan.protocol.NodeStatus)  # pylint: disable=no-member
        assert msg.message.mode == MODE_OPERATIONAL

    @staticmethod
    def test_vssc():
        """
        RaccoonLab specific test: 1 means Debug, 2 means Release.
        """
        node = DronecanNode()
        msg = node.sub_once(dronecan.uavcan.protocol.NodeStatus)  # pylint: disable=no-member
        assert msg.message.vendor_specific_status_code == VSSC_RACCOONLAB_RELEASE

    @staticmethod
    def test_publishing_period():
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
            msg = node.sub_once(dronecan.uavcan.protocol.NodeStatus)  # pylint: disable=no-member
            msgs.append(msg)
            timestamps.append(msg.timestamp)

        periods = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps) - 1)]
        for number in periods:
            assert pytest.approx(0.5, abs=0.05) == number

        uptame_elapsed = msgs[-1].message.uptime_sec - msgs[0].message.uptime_sec
        assert uptame_elapsed in [2, 3]

def main():
    print(os.path.abspath(__file__))
    subprocess.call(["pytest", os.path.abspath(__file__),
                     "-v",
                     '-W', 'ignore::DeprecationWarning'])

if __name__ == "__main__":
    main()
