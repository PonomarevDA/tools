#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import os
import sys
import asyncio
import logging
import numpy as np
import pycyphal.application

# pylint: disable=import-error
import uavcan.node.Heartbeat_1_0

from raccoonlab_tools.common.colorizer import Colorizer, Colors
from raccoonlab_tools.common.protocol_parser import CanProtocolParser, Protocol
from raccoonlab_tools.cyphal.utils import NodeFinder
from raccoonlab_tools.cyphal.service.actuator import Actuator
from raccoonlab_tools.cyphal.service.crct import CircuitStatus
from raccoonlab_tools.cyphal.service.gnss import Gnss
from raccoonlab_tools.cyphal.service.lights import Lights
from raccoonlab_tools.cyphal.service.barometer import Barometer
from raccoonlab_tools.cyphal.service.magnetometer import Magnetometer

class BaseMonitor:
    def __init__(self, node, node_id) -> None:
        assert isinstance(node, pycyphal.application._node_factory.SimpleNode)
        assert isinstance(node_id, int)
        self.services = []
        self.node = node
        self.node_id = node_id

    async def init(self):
        for service in self.services:
            await service.init()

    async def process(self):
        for service in self.services:
            service.print()

    @staticmethod
    def get_latest_sw_version() -> str:
        return ""

    @staticmethod
    def get_vssc_meaning(vssc : int) -> str:
        return f"{vssc} (meaning unknown)"


class GpsMagBaroMonitor(BaseMonitor):
    def __init__(self, node : pycyphal.application._node_factory.SimpleNode, node_id : int) -> None:
        super().__init__(node, node_id)

        self.services = [
            Gnss(node, node_id),
            Barometer(node, node_id),
            Magnetometer(node, node_id),
        ]

    @staticmethod
    def get_latest_sw_version() -> str:
        return "c78d47c3c9744f55"

    def get_vssc_meaning(self, vssc: int) -> str:
        bitmask = [
            "cyphal",
            "baro",
            "gps",
            "mag",
            "crct",
            "sys",
        ]

        errors = []
        for number, bit_meaning in enumerate(bitmask):
            if vssc & np.left_shift(1, number):
                errors.append(bit_meaning)

        if len(errors) > 0:
            string = ", ".join(str(error) for error in errors)
            string = f"{Colors.WARNING}{vssc}: ({string}){Colors.ENDC}"
        else:
            string = f"{vssc}"
        return string

class UavLightsMonitor(BaseMonitor):
    def __init__(self, node, node_id) -> None:
        super().__init__(node, node_id)
        self.node_id = node_id

        self.services = [
            Lights(node, node_id),
            CircuitStatus(node, node_id),
        ]

class MiniMonitor(BaseMonitor):
    def __init__(self, node : pycyphal.application._node_factory.SimpleNode, node_id : int) -> None:
        assert isinstance(node, pycyphal.application._node_factory.SimpleNode)
        assert isinstance(node_id, int)

        super().__init__(node, node_id)
        self.node_id = node_id

        self.services = [
            CircuitStatus(node, node_id),
            Actuator(node, node_id),
        ]


class PX4Monitor(BaseMonitor):
    def __init__(self, node, node_id) -> None:
        super().__init__(node, node_id)
        self.node_id = node_id
        self.services = [
            Actuator(node, node_id)
        ]


class RLConfigurator:
    def __init__(self) -> None:
        self.node_id = None
        self.heartbeat = uavcan.node.Heartbeat_1_0()

    async def main(self):
        self.node = pycyphal.application.make_node(uavcan.node.GetInfo_1_0.Response(
                uavcan.node.Version_1_0(major=1, minor=0),
                name="co.raccoonlab.spec_checker"
        ))
        self.node.heartbeat_publisher.mode = uavcan.node.Mode_1_0.OPERATIONAL
        self.node.start()

        heartbeat_sub = self.node.make_subscriber(uavcan.node.Heartbeat_1_0)
        heartbeat_sub.receive_in_background(self._heartbeat_callback)

        info, node_monitor = await self._find_node()

        await asyncio.sleep(0.1)
        while True:
            os.system('clear')
            print("RaccoonLab monitor")
            info.print_info(node_monitor.get_latest_sw_version())

            print("Node status:")
            print(f"- Health: {Colorizer.health_to_string(self.heartbeat.health.value)}")
            print(f"- Mode: {Colorizer.mode_to_string(self.heartbeat.mode.value)}")
            print(f"- VSSC: {node_monitor.get_vssc_meaning(self.heartbeat.vendor_specific_status_code)}")
            print(f"- Uptime: {self.heartbeat.uptime}")

            await node_monitor.process()
            await asyncio.sleep(0.1)

    async def _find_node(self) -> tuple:
        # 1. Define node ID
        node_finder = NodeFinder(self.node)
        self.node_id = await node_finder.find_online_node(timeout=5.0)
        while self.node_id is None:
            self.node_id = await node_finder.find_online_node(timeout=5.0)

        # 2. Define node name
        known_nodes = {
            'co.raccoonlab.gps_mag_baro' : GpsMagBaroMonitor,
            'co.raccoonlab.lights' : UavLightsMonitor,
            'PX4_FMU_V5' : PX4Monitor,
            'co.raccoonlab.mini' : MiniMonitor,
        }
        info = await node_finder.get_info()
        if info.name in known_nodes:
            node = known_nodes[info.name](self.node, self.node_id)
        else:
            print(f"Unknown node `{info.name}` has been found. Exit")
            sys.exit(0)

        print(f"Node `{info.name}` has been found.")
        await node.init()
        return info, node

    async def _heartbeat_callback(self, data, transfer_from):
        if self.node_id == transfer_from.source_node_id:
            self.heartbeat = data


def main():
    logging.getLogger("pycyphal").setLevel(logging.FATAL)
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        filename='rl_monitor.log',
                        filemode='w')
    CanProtocolParser.verify_protocol(white_list=[Protocol.CYPHAL], verbose=True)

    rl_configurator = RLConfigurator()
    try:
        asyncio.run(rl_configurator.main())
    except KeyboardInterrupt:
        print("Aborted by KeyboardInterrupt.")

if __name__ == "__main__":
    main()
