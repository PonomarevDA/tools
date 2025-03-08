#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
import asyncio
import pycyphal.application
import uavcan
import zubax.telega.CompactFeedback_1_0 as CompactFeedback_1_0
import reg.udral.physics.optics

async def heartbeat_callback(data, transfer_from):
    print(data)


def serialize_compact_feedback(voltage, current, rpm, demand_factor_pct):
    """
    uint11  dc_voltage                  [    0,+2047] * 0.2 = [     0,+409.4] volt
    int12   dc_current                  [-2048,+2047] * 0.2 = [-409.6,+409.4] ampere
    int12   phase_current_amplitude     ditto
    int13   velocity                    [-4096,+4095] radian/second (approx. [-39114,+39104] RPM)
    int8    demand_factor_pct           [ -128, +127] percent
    """
    dc_voltage = int(voltage * 5)
    dc_current = int(current * 5)
    velocity = int(rpm * 0.1047)
    demand_factor_pct = int(demand_factor_pct)
    return CompactFeedback_1_0(dc_voltage, dc_current, dc_current, velocity, demand_factor_pct)

async def main():
    node = pycyphal.application.make_node(
        uavcan.node.GetInfo_1_0.Response(
            uavcan.node.Version_1_0(major=1, minor=0),
            name="co.raccoonlab.spec_checker"
        )
    )

    node.start()

    feedback_publishers = [
        node.make_publisher(CompactFeedback_1_0, 3000),
        node.make_publisher(CompactFeedback_1_0, 3001),
        node.make_publisher(CompactFeedback_1_0, 3002),
        node.make_publisher(CompactFeedback_1_0, 3003),
    ]

    heartbeat_sub = node.make_subscriber(uavcan.node.Heartbeat_1_0)
    heartbeat_sub.receive_in_background(heartbeat_callback)

    for _ in range(1000):
        for fb_pub in feedback_publishers:
            await fb_pub.publish(serialize_compact_feedback(50.0, 0.5, 100, 5))
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Aborted by KeyboardInterrupt.")
