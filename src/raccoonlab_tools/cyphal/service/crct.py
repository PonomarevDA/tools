#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import asyncio
import logging
import pycyphal.application
# pylint: disable=import-error
import uavcan.node.GetInfo_1_0
import uavcan.si.sample.temperature.Scalar_1_0
import uavcan.si.sample.voltage.Scalar_1_0
from raccoonlab_tools.cyphal.topic import Subscriber

class CircuitStatusTemperatureSub(Subscriber):
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int,
                 def_id: int=2102,
                 reg_name=("uavcan.pub.crct.temp.id", "uavcan.pub.crct.temperature.id")) -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.si.sample.temperature.Scalar_1_0)
    def print_data(self):
        celcius = 0 if self.msg is None else round(self.msg.kelvin - 273.15, 0)
        print(f"- crct.temp ({self.port}): {celcius} Celcius")

class CircuitStatus5VSub(Subscriber):
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int,
                 def_id: int=2103,
                 reg_name="uavcan.pub.crct.5v.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.si.sample.voltage.Scalar_1_0)
    def print_data(self):
        volt = None if self.msg is None else round(self.msg.volt, 2)
        print(f"- crct.5v ({self.port}): {volt} Volt")

class CircuitStatusVinSub(Subscriber):
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int,
                 def_id: int=2104,
                 reg_name="uavcan.pub.crct.vin.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.si.sample.voltage.Scalar_1_0)
    def print_data(self):
        volt = None if self.msg is None else round(self.msg.volt, 2)
        print(f"- crct.vin ({self.port}): {volt} Volt")

class CircuitStatus:
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int) -> None:
        self.subs = [
            CircuitStatus5VSub(node=node, node_id=node_id),
            CircuitStatusVinSub(node=node, node_id=node_id),
            CircuitStatusTemperatureSub(node=node, node_id=node_id)
        ]

    async def init(self):
        for sub in self.subs:
            await sub.init()

    def print(self):
        print("CircuitStatus:")
        for sub in self.subs:
            sub.print_data()


async def test():
    node = pycyphal.application.make_node(uavcan.node.GetInfo_1_0.Response())
    node.start()

    service = CircuitStatus(node=node, node_id=50)
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
