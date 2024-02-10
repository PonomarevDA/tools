#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import asyncio
import pycyphal
import pycyphal.application
import uavcan.node
import uavcan.node.Heartbeat_1_0

async def main():
    node_info = uavcan.node.GetInfo_1_0.Response(
        uavcan.node.Version_1_0(major=1, minor=0),
        name="co.raccoonlab.example"
    )
    node = pycyphal.application.make_node(node_info)
    node.heartbeat_publisher.mode = uavcan.node.Mode_1_0.OPERATIONAL
    node.start()

    heartbeat_sub = node.make_subscriber(uavcan.node.Heartbeat_1_0)
    for _ in range(10):
        transfer_from = await heartbeat_sub.receive_for(1.1)
        print(transfer_from[0] if transfer_from is not None else None)

asyncio.run(main())
