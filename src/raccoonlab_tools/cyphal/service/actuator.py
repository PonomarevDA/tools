#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import math
import asyncio
import logging
import pycyphal.application
from raccoonlab_tools.cyphal.topic import Subscriber, Publisher
from raccoonlab_tools.common.colorizer import Colors, Colorizer

# pylint: disable=import-error
import uavcan.node.GetInfo_1_0
import reg.udral.service.actuator.common.sp.Vector4_0_1
import reg.udral.service.actuator.common.sp.Vector31_0_1
import reg.udral.service.actuator.common.Feedback_0_1
import reg.udral.service.common.Readiness_0_1

# temp, later these values should be randomly generated
SETPOINT_DEF_ID = 2342
READINESS_DEF_ID = 2343
FEEDBACK_DEF_ID = 2500

class SetpointSub(Subscriber):
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int,
                 def_id: int=SETPOINT_DEF_ID,
                 reg_name: str="uavcan.pub.udral.esc.0.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, reg.udral.service.actuator.common.sp.Vector31_0_1)
        self.max_recv_length = 0
    def print_data(self):
        if self.msg is None:
            data = "None"
        else:
            for idx in range(30, self.max_recv_length - 1, -1):
                is_zero = math.isclose(self.msg.value[idx], 0.0, rel_tol=1e-5)
                if not is_zero:
                    self.max_recv_length = idx + 1
                    break
            data = self.msg.value[0:self.max_recv_length]
        print(f"- udral.esc.0 ({self.port}): {data}")

class ReadinessSub(Subscriber):
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int,
                 def_id: int=READINESS_DEF_ID,
                 reg_name: str="uavcan.pub.udral.readiness.0.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, reg.udral.service.common.Readiness_0_1)
        self.max_recv_length = 0
    def print_data(self):
        mapping = {
            None:   "-",
            0:      "SLEEP = DISARMED",
            2:      "STANDBY = DISARMED",
            3:      Colorizer.okgreen("ENGAGED = ARMED"),
        }
        value = None if self.msg is None else self.msg.value
        print(f"- udral.readiness.0 ({self.port}): {value} ({mapping[value]})")

class FeedbackSub(Subscriber):
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int,
                 def_id: int=FEEDBACK_DEF_ID,
                 reg_name: str="uavcan.pub.feedback.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, reg.udral.service.actuator.common.Feedback_0_1)
        self.max_recv_length = 0
    def print_data(self):
        demand_factor_pct = None if self.msg is None else self.msg.demand_factor_pct
        print(f"- feedback ({self.port}): ({demand_factor_pct} %)")

class SetpointPub(Publisher):
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int,
                 rate) -> None:
        super().__init__(node=node,
                         node_id=node_id,
                         def_id=SETPOINT_DEF_ID,
                         reg_name="uavcan.sub.setpoint.id",
                         data_type=reg.udral.service.actuator.common.sp.Vector4_0_1,
                         rate=rate)

    def print_data(self):
        print(f"- setpoint ({self.port}): {self.msg.value}")

class ReadinessPub(Publisher):
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int,
                 rate) -> None:
        super().__init__(node=node,
                         node_id=node_id,
                         def_id=READINESS_DEF_ID,
                         reg_name="uavcan.sub.readiness.id",
                         data_type=reg.udral.service.common.Readiness_0_1,
                         rate=rate)

    def print_data(self):
        print(f"- readiness ({self.port}): {self.msg.value}")

class Actuator:
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int) -> None:
        self.subs = [
            SetpointSub(node=node, node_id=node_id),
            ReadinessSub(node=node, node_id=node_id),
            FeedbackSub(node=node, node_id=node_id),
        ]
        self.pubs = [
            SetpointPub(node=node, node_id=node_id, rate=50),
            ReadinessPub(node=node, node_id=node_id, rate=50),
        ]

    async def init(self):
        for topic in self.subs:
            await topic.init()
            print("")
        for topic in self.pubs:
            await topic.start_publishing()
            print("")

    def print(self):
        print("Actuator:")
        for topic in self.subs:
            if topic.msg is not None:
                topic.print_data()
        for topic in self.pubs:
            topic.print_data()

async def test():
    node = pycyphal.application.make_node(uavcan.node.GetInfo_1_0.Response())
    node.start()

    service = Actuator(node=node, node_id=50)
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
