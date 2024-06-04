#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import asyncio
import logging
import numpy as np
import pycyphal.application
# pylint: disable=import-error
import uavcan.si.sample.magnetic_field_strength.Vector3_1_1
from raccoonlab_tools.cyphal.topic import Subscriber
from raccoonlab_tools.common.colorizer import Colors

class MagnetometerSub(Subscriber):
    def __init__(self, node, node_id, def_id=2000, reg_name="uavcan.pub.zubax.mag.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.si.sample.magnetic_field_strength.Vector3_1_1)
        self.msg = None
    def print_data(self):
        if self.msg is not None:
            print(f"- zubax.mag ({self.port}:uavcan.si.sample.magnetic_field_strength.Vector3.1.1, {self.rate()} msg/sec):")
            mag_field = self.msg.ampere_per_meter.tolist()
            print(f"   Norm: {np.sqrt(np.sum(np.array(mag_field)**2)):.3f} A/m")
            print(f"   x: {mag_field[0]:.3f} A/m")
            print(f"   y: {mag_field[1]:.3f} A/m")
            print(f"   z: {mag_field[2]:.3f} A/m")
        else:
            print(f"{Colors.WARNING}NO DATA{Colors.ENDC}")

class Magnetometer:
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int) -> None:
        self.subs = [
            MagnetometerSub(node=node, node_id=node_id),
        ]

    async def init(self):
        for sub in self.subs:
            await sub.init()

    def print(self):
        print("MagneticFieldStrength:")
        for sub in self.subs:
            sub.print_data()

async def test():
    node = pycyphal.application.make_node(uavcan.node.GetInfo_1_0.Response())
    node.start()

    service = Magnetometer(node=node, node_id=50)
    await service.init()

    for _ in range(10):
        await asyncio.sleep(1.0)
        service.print()

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("pycyphal").setLevel(logging.FATAL)
    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print("Aborted by KeyboardInterrupt.")
