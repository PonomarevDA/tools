#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
import os
import sys
import subprocess
import pytest
import dronecan
import numpy as np

from raccoonlab_tools.dronecan.global_node import DronecanNode
from raccoonlab_tools.common.protocol_parser import CanProtocolParser, Protocol

@pytest.mark.dependency()
def test_transport():
    """
    This test is required just for optimization purposes.
    Let's skip all tests if we don't have an online Cyphal node.
    """
    assert CanProtocolParser.verify_protocol(white_list=[Protocol.DRONECAN])


@pytest.mark.dependency(depends=["test_transport"])
class TestGps:
    @staticmethod
    def test_sats():
        node = DronecanNode()
        transfer = node.sub_once(dronecan.uavcan.equipment.gnss.Fix2)  # pylint: disable=no-member
        assert transfer.message.sats_used >= 5

    @staticmethod
    def test_status_3d_fix():
        node = DronecanNode()
        transfer = node.sub_once(dronecan.uavcan.equipment.gnss.Fix2)  # pylint: disable=no-member
        assert transfer.message.status == 3


@pytest.mark.dependency(depends=["test_transport"])
class TestMagnetometer:
    @staticmethod
    def test_norm():
        """
        The magnitude of Earth's magnetic field at its surface ranges from 0.25 to 0.65 G.
        https://en.wikipedia.org/wiki/Earth%27s_magnetic_field
        """
        node = DronecanNode()
        # pylint: disable=no-member
        transfer = node.sub_once(dronecan.uavcan.equipment.ahrs.MagneticFieldStrength)
        field_vector_ga = np.array(transfer.transfer.payload.magnetic_field_ga)
        norm_ga = np.linalg.norm(field_vector_ga)
        assert 0.25 < norm_ga < 0.65


@pytest.mark.dependency(depends=["test_transport"])
class TestBarometer:
    @staticmethod
    def test_pressure():
        node = DronecanNode()
        # pylint: disable=no-member
        transfer = node.sub_once(dronecan.uavcan.equipment.air_data.StaticPressure)
        pressure_pascal = transfer.transfer.payload.static_pressure
        assert 80000 < pressure_pascal < 120000

    @staticmethod
    def test_temperature():
        node = DronecanNode()
        # pylint: disable=no-member
        transfer = node.sub_once(dronecan.uavcan.equipment.air_data.StaticTemperature)
        temperature_kelvin = transfer.transfer.payload.static_temperature
        assert (273-50) < temperature_kelvin < (273+50)


def main():
    cmd = ["pytest", os.path.abspath(__file__), "-v", '-W', 'ignore::DeprecationWarning']
    cmd += sys.argv[1:]
    subprocess.call(cmd)

if __name__ == "__main__":
    main()
