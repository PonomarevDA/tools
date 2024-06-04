#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import asyncio
import logging
import pycyphal.application
# pylint: disable=import-error
import uavcan.si.sample.pressure.Scalar_1_0
import uavcan.si.sample.temperature.Scalar_1_0
from raccoonlab_tools.cyphal.topic import Subscriber


class BaroPressureSub(Subscriber):
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int,
                 def_id: int=2100,
                 reg_name="uavcan.pub.zubax.baro.press.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.si.sample.pressure.Scalar_1_0)
    def print_data(self):
        value = self.msg.pascal if self.msg is not None else 0.0
        print(f"- zubax.baro.press ({self.port}:uavcan.si.sample.pressure.Scalar_1.0, {self.rate()} msg/sec): {value:.2f} Pascal")

class BaroTemperatureSub(Subscriber):
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int,
                 def_id: int=2101, 
                 reg_name="uavcan.pub.zubax.baro.temp.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.si.sample.temperature.Scalar_1_0)
    def print_data(self):
        value = self.msg.kelvin if self.msg is not None else 0.0
        print(f"- zubax.baro.temp ({self.port}:uavcan.si.sample.temperature.Scalar_1.0, {self.rate()} msg/sec): {value:.2f} Kelvin")

class Barometer:
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int) -> None:
        self.subs = [
            BaroPressureSub(node=node, node_id=node_id),
            BaroTemperatureSub(node=node, node_id=node_id),
        ]


    async def init(self):
        for sub in self.subs:
            await sub.init()

    def print(self):
        print("Barometer:")
        for sub in self.subs:
            sub.print_data()


async def test():
    node = pycyphal.application.make_node(uavcan.node.GetInfo_1_0.Response())
    node.start()

    service = Barometer(node=node, node_id=50)
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
