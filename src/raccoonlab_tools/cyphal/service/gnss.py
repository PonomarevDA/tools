#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import asyncio
import logging
import datetime
import pycyphal.application
# pylint: disable=import-error
import uavcan.primitive.scalar.Integer16_1_0
import uavcan.time.SynchronizedTimestamp_1_0
import reg.udral.physics.kinematics.geodetic.PointStateVarTs_0_1 as PointStateVarTs_0_1
import ds015.service.gnss.Gnss_0_1
import ds015.service.gnss.Covariance_0_1
from raccoonlab_tools.cyphal.topic import Subscriber
from raccoonlab_tools.common.colorizer import Colorizer


GPS_DEF_PORTS = {
    'cov': 2405,
    'point': 2406,
    'sats': 2407,
    'status': 2408,
    'pdop': 2409,
}

class ZubaxGpsPointSub(Subscriber):
    def __init__(self, node, node_id, def_id=GPS_DEF_PORTS['point'], reg_name="uavcan.pub.zubax.gps.point.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, PointStateVarTs_0_1)
        self.str_data_type = "reg.udral.physics.kinematics.geodetic.PointStateVarTs.0.1"
    def print_data(self):
        print(f"- zubax.gps.point ({self.port}:{self.str_data_type}, {self.rate()} msg/sec)")

class ZubaxGpsSatsSub(Subscriber):
    def __init__(self, node, node_id, def_id=GPS_DEF_PORTS['sats'], reg_name="uavcan.pub.zubax.gps.sats.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.primitive.scalar.Integer16_1_0)
        self.str_data_type = "uavcan.primitive.scalar.Integer16.1.0"
    def print_data(self):
        value = self.msg.value if self.msg is not None else None
        if value == 0:
            value = Colorizer.header(value)
        print(f"- zubax.gps.sats ({self.port}:{self.str_data_type}, {self.rate()} msg/sec): {value}")

class ZubaxGpsPdopSub(Subscriber):
    def __init__(self, node, node_id, def_id=GPS_DEF_PORTS['pdop'], reg_name="uavcan.pub.zubax.gps.pdop.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.primitive.scalar.Real32_1_0)
    def print_data(self):
        value = self.msg.value if self.msg is not None else 0.0
        print(f"- zubax.gps.pdop ({self.port}:uavcan.primitive.scalar.Integer16.1.0): {value:.2f}")

class ZubaxGpsStatusSub(Subscriber):
    def __init__(self, node, node_id, def_id=GPS_DEF_PORTS['status'], reg_name="uavcan.pub.zubax.gps.status.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.primitive.scalar.Integer16_1_0)
    def print_data(self):
        value = self.msg.value if self.msg is not None else None
        INT_TO_STR = {
            0 : "NO FIX (0)",
            1 : "TIME_ONLY (1)",
            2 : "2D_FIX (2)",
            3 : "3D_FIX (3)",
        }
        if value in INT_TO_STR:
            value = INT_TO_STR[value]
        print(f"- zubax.gps.status ({self.port}:uavcan.primitive.scalar.Integer16.1.0, {self.rate()} msg/sec): {value}")

class DS015GpsGnssSub(Subscriber):
    def __init__(self, node, node_id, def_id=2005, reg_name="uavcan.pub.ds015.gps.gnss.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, ds015.service.gnss.Gnss_0_1)
    def print_data(self):
        SPOOFING_INT_TO_STR = {
            0 : "UNKNOWN (0)",
            1 : "NO_SPOOFING_INDICATED (1)",
            2 : "SPOOFING_INDICATED (2)",
            3 : "MULTIPLE_SPOOFING_INDICATIONS (3)",
        }
        try:
            jamming_state = self.msg.status.jamming_state
            spoofing_state = SPOOFING_INT_TO_STR.get(self.msg.status.spoofing_state)
        except Exception as err:
            jamming_state = err
            spoofing_state = "err2"

        print(f"- ds015.gps.gnss ({self.port}:ds015.service.gnss.Gnss.0.1, {self.rate()} msg/sec)")
        if self.msg is None:
            return

        print(f"    alt {self.msg.point.altitude.meter:.2f} (from {self.min.point.altitude.meter:.2f} to {self.max.point.altitude.meter:.2f})\n"
              f"    hdop {self.msg.hdop:.2f} (from {self.min.hdop:.2f} to {self.max.hdop:.2f})\n"
              f"    vdop {self.msg.vdop:.2f} (from {self.min.vdop:.2f} to {self.max.vdop:.2f})\n"
              f"    eph {self.msg.horizontal_accuracy:.2f} (from {self.min.horizontal_accuracy:.2f} to {self.max.horizontal_accuracy:.2f})\n"
              f"    epv {self.msg.vertical_accuracy:.2f} (from {self.min.vertical_accuracy:.2f} to {self.max.vertical_accuracy:.2f})\n"
              f"    jamming_state {jamming_state}\n"
              f"    spoofing_state {spoofing_state}"
        )

class DS015GpsCovSub(Subscriber):
    def __init__(self, node, node_id, def_id=GPS_DEF_PORTS['cov'], reg_name="uavcan.pub.ds015.gps.cov.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, ds015.service.gnss.Covariance_0_1)
    def print_data(self):
        print(f"- ds015.gps.cov ({self.port}:ds015.service.gnss.Covariance.0.1, {self.rate()} msg/sec):")
        try:
            pos = self.msg.point_covariance_urt
            vel = self.msg.velocity_covariance_urt
            print(
                "  Position NED [m^2]                  Velocity NED [m^2/s^2]\n"
                f"  {pos[0]:>10,.3E} {pos[1]:>10,.3E} {pos[2]:>10,.3E}  "
                f"  {vel[0]:>10,.3E} {vel[1]:>10,.3E} {vel[2]:>10,.3E}\n"
                f"  {pos[1]:>10,.3E} {pos[3]:>10,.3E} {pos[4]:>10,.3E}  "
                f"  {vel[1]:>10,.3E} {vel[3]:>10,.3E} {vel[4]:>10,.3E}\n"
                f"  {pos[2]:>10,.3E} {pos[4]:>10,.3E} {pos[5]:>10,.3E}  "
                f"  {vel[2]:>10,.3E} {vel[4]:>10,.3E} {vel[5]:>10,.3E}"
            )
        except Exception:
            pass

class GpsTimeUtcSub(Subscriber):
    def __init__(self, node, node_id, def_id=2002, reg_name="uavcan.pub.gps.time_utc.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.time.SynchronizedTimestamp_1_0)
    def print_data(self):
        seconds = int(self.msg.microsecond / 1000000) if self.msg is not None else 0
        print(f"- time_utc ({self.port}): {seconds} ({datetime.datetime.fromtimestamp(seconds)})")

class Gnss:
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int) -> None:
        self.subs = [
            ZubaxGpsPointSub(node=node, node_id=node_id),
            ZubaxGpsSatsSub(node=node, node_id=node_id),
            ZubaxGpsPdopSub(node=node, node_id=node_id),
            ZubaxGpsStatusSub(node=node, node_id=node_id),
            DS015GpsGnssSub(node=node, node_id=node_id),
            DS015GpsCovSub(node=node, node_id=node_id),
            GpsTimeUtcSub(node=node, node_id=node_id),
        ]

    async def init(self):
        for sub in self.subs:
            await sub.init()

    def print(self):
        print("Gnss:")
        for sub in self.subs:
            sub.print_data()

async def test():
    node = pycyphal.application.make_node(uavcan.node.GetInfo_1_0.Response())
    node.start()

    service = Gnss(node=node, node_id=50)
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
