#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import asyncio
import logging
import secrets
import pycyphal.application
# pylint: disable=import-error
import uavcan.node.GetInfo_1_0
import reg.udral.physics.optics.HighColor_0_1
from raccoonlab_tools.cyphal.topic import Publisher

class HighColorPub(Publisher):
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int,
                 rate) -> None:
        super().__init__(node=node,
                         node_id=node_id,
                         def_id=2107,
                         reg_name="uavcan.sub.readiness.id",
                         data_type=reg.udral.physics.optics.HighColor_0_1,
                         rate=rate)
        self.red = int(0)
        self.green = int(0)
        self.blue = int(0)
    async def init(self):
        self._pub = self.node.make_publisher(reg.udral.physics.optics.HighColor_0_1, 2107)
        self._pub_counter = 0
    async def publish_and_print(self):
        self.red += secrets.randbelow(2)
        self.green += secrets.randbelow(3)
        self.blue += secrets.randbelow(2)

        self.msg.red   = self.red   % 32 if self.red   % 64  < 32 else 63 -  self.red   % 64
        self.msg.green = self.green % 64 if self.green % 128 < 64 else 127 - self.green % 128
        self.msg.blue  = self.blue  % 32 if self.blue  % 64  < 32 else 63 -  self.blue  % 64
        print(f"- HighColor: red={self.msg.red}, green={self.msg.green}, blue={self.msg.blue}")
        self._pub_counter += 1
        await self._pub.publish(self.msg)

class Lights:
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int) -> None:
        self.pubs = [
            HighColorPub(node=node, node_id=node_id, rate=50),
        ]

    async def init(self):
        for topic in self.pubs:
            await topic.start_publishing()
            print("")

    def print(self):
        print("Lights:")
        for topic in self.pubs:
            topic.print_data()

async def test():
    node = pycyphal.application.make_node(uavcan.node.GetInfo_1_0.Response())
    node.start()

    service = Lights(node=node, node_id=50)
    await service.init()

    for _ in range(100):
        await asyncio.sleep(0.5)
        await service.print()


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("pycyphal").setLevel(logging.FATAL)
    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print("Aborted by KeyboardInterrupt.")
