#!/usr/bin/env python3

import os
import sys
import subprocess
# pylint: disable=no-member
import dronecan
import pytest

from raccoonlab_tools.dronecan.global_node import DronecanNode
from raccoonlab_tools.common.protocol_parser import CanProtocolParser, Protocol
from raccoonlab_tools.dronecan.utils import NodeFinder

TEMPERATURE_MIN = 273
TEMPERATURE_MAX = 323
ERROR_FLAGS = 0
VOLTAGE_5V_MIN = 4.5
VOLTAGE_5V_MAX = 5.5
VOLTAGE_VIN_MIN = 4.5
VOLTAGE_VIN_MAX = 55
FILTER_5V = lambda msg : msg.message.circuit_id == CIRCUIT_5V_ID
FILTER_VIN = lambda msg : msg.message.circuit_id == CIRCUIT_VIN_ID


@pytest.mark.dependency()
def test_node_existance():
    """
    This test is required just for optimization purposes.
    Let's skip all tests if we don't have an online Cyphal node.
    """
    global DEVICE_ID, CIRCUIT_5V_ID, CIRCUIT_VIN_ID

    assert CanProtocolParser.verify_protocol(white_list=[Protocol.DRONECAN])
    DEVICE_ID = NodeFinder().find_online_node()
    CIRCUIT_5V_ID = DEVICE_ID * 10
    CIRCUIT_VIN_ID = DEVICE_ID * 10 + 1

@pytest.mark.dependency(depends=["test_node_existance"])
class TestDeviceTemperature:

    @staticmethod
    def test_temperature():
        node = DronecanNode()
        msg = node.sub_once(dronecan.uavcan.equipment.device.Temperature)
        assert TEMPERATURE_MIN <= msg.message.temperature <= TEMPERATURE_MAX

    @staticmethod
    def test_device_id():
        node = DronecanNode()
        msg = node.sub_once(dronecan.uavcan.equipment.device.Temperature)
        assert msg.message.device_id == DEVICE_ID

    @staticmethod
    def test_error_flags():
        node = DronecanNode()
        msg = node.sub_once(dronecan.uavcan.equipment.device.Temperature)
        assert msg.message.error_flags == ERROR_FLAGS

@pytest.mark.dependency(depends=["test_node_existance"])
class TestCircuitStatus:

    @staticmethod
    def test_circuit_5v_id():
        node = DronecanNode()
        msg = node.sub_once(dronecan.uavcan.equipment.power.CircuitStatus, FILTER_5V,
                            timeout_sec=2.5)
        assert msg.message.circuit_id == CIRCUIT_5V_ID

    @staticmethod
    def test_circuit_vin_id():
        node = DronecanNode()
        msg = node.sub_once(dronecan.uavcan.equipment.power.CircuitStatus, FILTER_VIN,
                            timeout_sec=2.5)
        assert msg.message.circuit_id == CIRCUIT_VIN_ID

    @staticmethod
    def test_voltage_5v():
        node = DronecanNode()
        msg = node.sub_once(dronecan.uavcan.equipment.power.CircuitStatus, FILTER_5V,
                            timeout_sec=2.5)
        assert VOLTAGE_5V_MIN <= msg.message.voltage <= VOLTAGE_5V_MAX

    @staticmethod
    def test_voltage_vin():
        node = DronecanNode()
        msg = node.sub_once(dronecan.uavcan.equipment.power.CircuitStatus, FILTER_VIN,
                            timeout_sec=2.5)
        assert VOLTAGE_VIN_MIN <= msg.message.voltage <= VOLTAGE_VIN_MAX

    @staticmethod
    def test_error_flags_5v():
        node = DronecanNode()
        msg = node.sub_once(dronecan.uavcan.equipment.power.CircuitStatus, FILTER_5V,
                            timeout_sec=2.5)
        assert msg.message.error_flags == ERROR_FLAGS

    @staticmethod
    def test_error_flags_vin():
        node = DronecanNode()
        msg = node.sub_once(dronecan.uavcan.equipment.power.CircuitStatus, FILTER_VIN,
                            timeout_sec=2.5)
        assert msg.message.error_flags == ERROR_FLAGS

def main():

    cmd = ["pytest", os.path.abspath(__file__), "-v", '-W', 'ignore::DeprecationWarning']
    cmd += sys.argv[1:]
    sys.exit(subprocess.call(cmd))

if __name__ == "__main__":
    main()
