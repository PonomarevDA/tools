#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import os
import sys
import time
import datetime
import math
import asyncio
import numpy as np
import secrets

import pycyphal.application

# pylint: disable=import-error
import uavcan.register.Access_1_0
import uavcan.node.Heartbeat_1_0
import uavcan.primitive.array.Natural16_1_0

import uavcan.si.sample.pressure.Scalar_1_0
import uavcan.si.sample.temperature.Scalar_1_0
import uavcan.si.sample.voltage.Scalar_1_0
import uavcan.si.sample.magnetic_field_strength.Vector3_1_1
import uavcan.primitive.scalar.Integer16_1_0
import uavcan.time.SynchronizedTimestamp_1_0

import reg.udral.physics.optics.HighColor_0_1
import reg.udral.service.actuator.common.sp.Vector31_0_1
import reg.udral.service.common.Readiness_0_1

import ds015.service.gnss.Gnss_0_1
import ds015.service.gnss.Covariance_0_1

from raccoonlab_tools.scripts.rl_monitor.base_subscriber import BaseSubscriber
from raccoonlab_tools.common.colorizer import Colorizer, Colors
from raccoonlab_tools.cyphal.utils import NodeFinder
from raccoonlab_tools.common.protocol_parser import CanProtocolParser, Protocol


class HighColorPub:
    def __init__(self, node : pycyphal.application._node_factory.SimpleNode, node_id : int) -> None:
        assert isinstance(node, pycyphal.application._node_factory.SimpleNode)
        assert isinstance(node_id, int)
        self.node = node
        self.node_id = node_id
        self.msg = reg.udral.physics.optics.HighColor_0_1()
        self.red = int(0)
        self.green = int(0)
        self.blue = int(0)
    async def init_pub(self):
        self._pub = self.node.make_publisher(reg.udral.physics.optics.HighColor_0_1, 2107)
        self._pub_counter = 0
    async def publish_and_print(self):
        self.red += secrets.randbelow(2)
        self.green += secrets.randbelow(3)
        self.blue += secrets.randbelow(2)

        self.msg.red   = self.red   % 32 if self.red   % 64  < 32 else 63 -  self.red   % 64
        self.msg.green = self.green % 64 if self.green % 128 < 64 else 127 - self.green % 128
        self.msg.blue  = self.blue  % 32 if self.blue  % 64  < 32 else 63 -  self.blue  % 64
        print("Lights:")
        print(f"- HighColor: red={self.msg.red}, green={self.msg.green}, blue={self.msg.blue}")
        self._pub_counter += 1
        await self._pub.publish(self.msg)


class CircuitStatusTemperatureSub(BaseSubscriber):
    def __init__(self,
                 node,
                 node_id,
                 def_id=2102,
                 reg_name=("uavcan.pub.crct.temp.id", "uavcan.pub.crct.temperature.id")) -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.si.sample.temperature.Scalar_1_0)
    def print_data(self):
        print("CircuitStatus:")
        if self.data is not None:
            kelvin = self.data.kelvin
            celcius = kelvin - 273
        else:
            kelvin = 0
            celcius = 0
        print(f"- crct.temp ({self.get_id_string()}): {kelvin} Kelvin ({celcius} Celcius)")

class CircuitStatus5VSub(BaseSubscriber):
    def __init__(self, node, node_id, def_id=2103, reg_name="uavcan.pub.crct.5v.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.si.sample.voltage.Scalar_1_0)
    def print_data(self):
        volt = None if self.data is None else round(self.data.volt, 2)
        print(f"- crct.5v ({self.get_id_string()}): {volt} Volt")

class CircuitStatusVinSub(BaseSubscriber):
    def __init__(self, node, node_id, def_id=2104, reg_name="uavcan.pub.crct.vin.id") -> None:
        assert isinstance(node, pycyphal.application._node_factory.SimpleNode)
        assert isinstance(node_id, int)
        super().__init__(node, node_id, def_id, reg_name, uavcan.si.sample.voltage.Scalar_1_0)
    def print_data(self):
        volt = None if self.data is None else round(self.data.volt, 2)
        print(f"- crct.vin ({self.get_id_string()}): {volt} Volt")

GPS_DEF_PORTS = {
    'cov': 2405,
    'point': 2406,
    'sats': 2407,
    'status': 2408,
    'pdop': 2409,
}

class ZubaxGpsSatsSub(BaseSubscriber):
    def __init__(self, node, node_id, def_id=GPS_DEF_PORTS['sats'], reg_name="uavcan.pub.zubax.gps.sats.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.primitive.scalar.Integer16_1_0)
        self.str_data_type = "uavcan.primitive.scalar.Integer16.1.0"
    def print_data(self):
        print("GNSS:")

        value = self.data.value if self.data is not None else None
        if value == 0:
            value = Colorizer.header(value)
        print(f"- zubax.gps.sats ({self.get_id_string()}:{self.str_data_type}, {self.rate()} msg/sec): {value}")

class ZubaxGpsPdopSub(BaseSubscriber):
    def __init__(self, node, node_id, def_id=GPS_DEF_PORTS['pdop'], reg_name="uavcan.pub.zubax.gps.pdop.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.primitive.scalar.Real32_1_0)
    def print_data(self):
        value = self.data.value if self.data is not None else 0.0
        print(f"- zubax.gps.pdop ({self.get_id_string()}:uavcan.primitive.scalar.Integer16.1.0): {value:.2f}")

class ZubaxGpsStatusSub(BaseSubscriber):
    def __init__(self, node, node_id, def_id=GPS_DEF_PORTS['status'], reg_name="uavcan.pub.zubax.gps.status.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.primitive.scalar.Integer16_1_0)
    def print_data(self):
        value = self.data.value if self.data is not None else None
        INT_TO_STR = {
            0 : "NO FIX (0)",
            1 : "TIME_ONLY (1)",
            2 : "2D_FIX (2)",
            3 : "3D_FIX (3)",
        }
        if value in INT_TO_STR:
            value = INT_TO_STR[value]
        print(f"- zubax.gps.status ({self.get_id_string()}:uavcan.primitive.scalar.Integer16.1.0, {self.rate()} msg/sec): {value}")

class DS015GpsGnssSub(BaseSubscriber):
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
            jamming_state = self.data.status.jamming_state
            spoofing_state = SPOOFING_INT_TO_STR.get(self.data.status.spoofing_state)
        except Exception as err:
            jamming_state = err
            spoofing_state = "err2"

        print(f"- ds015.gps.gnss ({self.get_id_string()}:ds015.service.gnss.Gnss.0.1, {self.rate()} msg/sec):\n"
              f"    jamming_state {jamming_state}\n"
              f"    spoofing_state {spoofing_state}"
        )

class DS015GpsCovSub(BaseSubscriber):
    def __init__(self, node, node_id, def_id=GPS_DEF_PORTS['cov'], reg_name="uavcan.pub.ds015.gps.cov.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, ds015.service.gnss.Covariance_0_1)
    def print_data(self):
        print(f"- ds015.gps.cov ({self.get_id_string()}:ds015.service.gnss.Covariance.0.1, {self.rate()} msg/sec):")
        try:
            pos = self.data.point_covariance_urt
            vel = self.data.velocity_covariance_urt
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

class GpsTimeUtcSub(BaseSubscriber):
    def __init__(self, node, node_id, def_id=2002, reg_name="uavcan.pub.gps.time_utc.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.time.SynchronizedTimestamp_1_0)
    def print_data(self):
        seconds = int(self.data.microsecond / 1000000) if self.data is not None else 0
        print(f"- time_utc ({self.get_id_string()}): {seconds} ({datetime.datetime.fromtimestamp(seconds)})")

class MagnetometerSub(BaseSubscriber):
    def __init__(self, node, node_id, def_id=2000, reg_name="uavcan.pub.zubax.mag.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.si.sample.magnetic_field_strength.Vector3_1_1)
        self.data = None
    def print_data(self):
        print("MagneticFieldStrength:")
        if self.data is not None:
            print(f"- zubax.mag ({self.get_id_string()}:uavcan.si.sample.magnetic_field_strength.Vector3.1.1, {self.rate()} msg/sec):")
            mag_field = self.data.ampere_per_meter.tolist()
            print(f"   Norm: {np.sqrt(np.sum(np.array(mag_field)**2)):.3f} A/m")
            print(f"   x: {mag_field[0]:.3f} A/m")
            print(f"   y: {mag_field[1]:.3f} A/m")
            print(f"   z: {mag_field[2]:.3f} A/m")
        else:
            print(f"{Colors.WARNING}NO DATA{Colors.ENDC}")

class BaroPressureSub(BaseSubscriber):
    def __init__(self, node, node_id, def_id=2100, reg_name="uavcan.pub.zubax.baro.press.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.si.sample.pressure.Scalar_1_0)
    def print_data(self):
        print("Barometer:")
        value = self.data.pascal if self.data is not None else 0.0
        print(f"- zubax.baro.press ({self.get_id_string()}:uavcan.si.sample.pressure.Scalar_1.0, {self.rate()} msg/sec): {value:.2f} Pascal")

class BaroTemperatureSub(BaseSubscriber):
    def __init__(self, node, node_id, def_id=2101, reg_name="uavcan.pub.zubax.baro.temp.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, uavcan.si.sample.temperature.Scalar_1_0)
    def print_data(self):
        value = self.data.kelvin if self.data is not None else 0.0
        print(f"- zubax.baro.temp ({self.get_id_string()}:uavcan.si.sample.temperature.Scalar_1.0, {self.rate()} msg/sec): {value:.2f} Kelvin")

class SetpointSub(BaseSubscriber):
    def __init__(self, node, node_id, def_id=2342, reg_name="uavcan.pub.udral.esc.0.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, reg.udral.service.actuator.common.sp.Vector31_0_1)
        self.max_recv_length = 0
    def print_data(self):
        for idx in range(30, self.max_recv_length - 1, -1):
            is_zero = math.isclose(self.data.value[idx], 0.0, rel_tol=1e-5)
            if not is_zero:
                self.max_recv_length = idx + 1
                break
        print("Actuators:")
        print(f"- udral.esc.0 ({self.get_id_string()}): {self.data.value[0:self.max_recv_length]}")

class ReadinessSub(BaseSubscriber):
    def __init__(self, node, node_id, def_id=2343, reg_name="uavcan.pub.udral.readiness.0.id") -> None:
        super().__init__(node, node_id, def_id, reg_name, reg.udral.service.common.Readiness_0_1)
        self.max_recv_length = 0
    def print_data(self):
        mapping = {
            None:   "-",
            0:      "SLEEP = DISARMED",
            2:      "STANDBY = DISARMED",
            3:      Colorizer.okgreen("ENGAGED = ARMED"),
        }
        value = self.data.value
        print(f"- udral.readiness.0 ({self.get_id_string()}): {value} ({mapping[value]})")

class BaseMonitor:
    def __init__(self, node, node_id) -> None:
        assert isinstance(node, pycyphal.application._node_factory.SimpleNode)
        assert isinstance(node_id, int)
        self.subs = []
        self.pubs = []
        self.node = node
        self.node_id = node_id

    async def init(self):
        for sub in self.subs:
            await sub.init_sub()
        for pub in self.pubs:
            await pub.init_pub()

    async def process(self):
        for pub in self.pubs:
            await pub.publish_and_print()
        for sub in self.subs:
            sub.print_data()

    @staticmethod
    def get_latest_sw_version() -> str:
        return ""

    @staticmethod
    def get_vssc_meaning(vssc : int) -> str:
        return f"{vssc} (meaning unknown)"


class GpsMagBaroMonitor(BaseMonitor):
    def __init__(self, node : pycyphal.application._node_factory.SimpleNode, node_id : int) -> None:
        super().__init__(node, node_id)

        self.subs = [
            ZubaxGpsSatsSub(node, node_id),
            ZubaxGpsPdopSub(node, node_id),
            ZubaxGpsStatusSub(node, node_id),
            DS015GpsGnssSub(node, node_id),
            DS015GpsCovSub(node, node_id),
            GpsTimeUtcSub(node, node_id),
            MagnetometerSub(node, node_id),
            BaroPressureSub(node, node_id),
            BaroTemperatureSub(node, node_id)
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

        self.subs = [
            CircuitStatusTemperatureSub(node, node_id),
        ]

        self.pubs = [
            HighColorPub(node, node_id),
        ]

class MiniMonitor(BaseMonitor):
    def __init__(self, node : pycyphal.application._node_factory.SimpleNode, node_id : int) -> None:
        assert isinstance(node, pycyphal.application._node_factory.SimpleNode)
        assert isinstance(node_id, int)

        super().__init__(node, node_id)
        self.node_id = node_id

        self.subs = [
            CircuitStatusTemperatureSub(node, node_id),
            CircuitStatus5VSub(node, node_id),
            CircuitStatusVinSub(node, node_id),
        ]


class PX4Monitor(BaseMonitor):
    def __init__(self, node, node_id) -> None:
        super().__init__(node, node_id)
        self.node_id = node_id
        self.subs = [
            SetpointSub(node, node_id),
            ReadinessSub(node, node_id),
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
    CanProtocolParser.verify_protocol(white_list=[Protocol.CYPHAL], verbose=True)

    rl_configurator = RLConfigurator()
    try:
        asyncio.run(rl_configurator.main())
    except KeyboardInterrupt:
        print("Aborted by KeyboardInterrupt.")

if __name__ == "__main__":
    main()
