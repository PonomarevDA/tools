#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
"""
Test DroneCAN node specification compliance.
1. NodeStatus publising rate 2 Hz
2. NodeStatus.health = HEALTH_OK
3. NodeStatus.mode = MODE_OPERATIONAL
4. NodeStatus.vendor_specific_status_code = 0

Dependencies: dronecan setuptools pytest pyserial netifaces python-can pytest-dependency
"""
import os
import sys
import subprocess
import argparse

import dronecan
import pytest

from raccoonlab_tools.dronecan.global_node import DronecanNode
from raccoonlab_tools.common.protocol_parser import (
    CanProtocolParser,
    Protocol,
    ProtocolVerificationError,
)
from raccoonlab_tools.common.device_manager import DeviceManager, TransportNotFoundException

HEALTH_OK = 0
MODE_OPERATIONAL = 0

@pytest.mark.dependency(name="get_device_port")
def test_get_device_port():
    """
    Let's skip all next tests if we don't have an online DroneCAN node.
    """
    try:
        device_port = DeviceManager.get_device_port()
    except TransportNotFoundException:
        device_port = None

    assert isinstance(device_port, str), "A transport couldn't be found"

@pytest.mark.dependency(name="verify_protocol", depends=["get_device_port"])
def test_verify_protocol():
    try:
        protocol = CanProtocolParser.verify_protocol(white_list=[Protocol.DRONECAN])
    except ProtocolVerificationError:
        protocol = None

    assert protocol == Protocol.DRONECAN, "There is no any online DroneCAN node"

@pytest.mark.dependency(depends=["verify_protocol"])
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
        node = DronecanNode()
        msg = node.sub_once(dronecan.uavcan.protocol.NodeStatus)  # pylint: disable=no-member
        assert msg.message.vendor_specific_status_code == 0

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
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.parse_args()

    cmd = ["pytest", os.path.abspath(__file__)]
    cmd += ["-v"]  # Increase verbosity
    cmd += ["-W", "ignore::DeprecationWarning"]  # Ignore specific warnings

    sys.exit(subprocess.call(cmd))

if __name__ == "__main__":
    main()
