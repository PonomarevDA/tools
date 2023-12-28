#!/usr/bin/env python3
import os
import sys
import time
import datetime
import asyncio
import pathlib
import numpy as np
import random


repo_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_dir / "build/nunavut_out"))
sys.path.insert(0, str(repo_dir / "cyphal"))
# pylint: disable=import-error
import uavcan.register.Access_1_0
import uavcan.node.Heartbeat_1_0
import uavcan.primitive.array.Natural16_1_0

import uavcan.si.sample.pressure.Scalar_1_0
import uavcan.si.sample.temperature.Scalar_1_0
import uavcan.si.sample.magnetic_field_strength.Vector3_1_1
import uavcan.primitive.scalar.Integer16_1_0
import uavcan.time.SynchronizedTimestamp_1_0

import reg.udral.physics.optics.HighColor_0_1

from utils import CyphalTools

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Colorizer:
    @staticmethod
    def normal(origin_string):
        return origin_string

    @staticmethod
    def header(origin_string):
        """Purple"""
        return f"{Colors.HEADER}{origin_string}{Colors.ENDC}"

    @staticmethod
    def warning(origin_string):
        "Orange"
        return f"{Colors.WARNING}{origin_string}{Colors.ENDC}"

    @staticmethod
    def okcyan(origin_string):
        return f"{Colors.OKCYAN}{origin_string}{Colors.ENDC}"

async def getset_port_id(node_id, callback, def_id, reg_name, data_type):
    assert isinstance(def_id, int)
    print(node_id, def_id, reg_name, data_type)
    cyphal_node = await CyphalTools.get_node()
    access_client = cyphal_node.make_client(uavcan.register.Access_1_0, node_id)

    id = await CyphalTools.get_port_id_reg_value(node_id, reg_name)
    assert id is not None, f"{reg_name} is not exist"
    need_update = (id == 0) or (id > 8191)

    if need_update:
        set_request = uavcan.register.Access_1_0.Request()
        set_request.name.name = reg_name
        set_request.value.natural16 = uavcan.primitive.array.Natural16_1_0(def_id)
        await access_client.call(set_request)
        id = def_id
    assert isinstance(id, int), reg_name
    mag_sub = cyphal_node.make_subscriber(data_type, id)
    mag_sub.receive_in_background(callback)
    access_client.close()

    return id, need_update

class HighColorPub:
    def __init__(self, node_id) -> None:
        self.node_id = node_id
        self.msg = reg.udral.physics.optics.HighColor_0_1()
        self.red = int(0)
        self.green = int(0)
        self.blue = int(0)
    async def init(self):
        cyphal_node = await CyphalTools.get_node()
        self._pub = cyphal_node.make_publisher(reg.udral.physics.optics.HighColor_0_1, 2107)
        self._pub_counter = 0
        # self._id, self.id_updated = await getset_port_id(
        #     self.node_id,
        #     self.callback,
        #     def_id=self.def_id,
        #     reg_name=self.reg_name,
        #     data_type=self.data_type
        # )
    async def process_publisher(self):
        self.red += random.randint(0,1)
        self.green += random.randint(0,2)
        self.blue += random.randint(0,1)

        self.msg.red   = self.red   % 32 if self.red   % 64  < 32 else 63 -  self.red   % 64
        self.msg.green = self.green % 64 if self.green % 128 < 64 else 127 - self.green % 128
        self.msg.blue  = self.blue  % 32 if self.blue  % 64  < 32 else 63 -  self.blue  % 64
        print(f"Lights:")
        print(f"- HighColor: red={self.msg.red}, green={self.msg.green}, blue={self.msg.blue}")
        self._pub_counter += 1
        await self._pub.publish(self.msg)


class BaseSubscriber:
    def __init__(self, node_id, def_id, reg_name, data_type) -> None:
        self.data = None
        self._id = None
        self.id_updated = False
        self.node_id = node_id
        self.def_id = def_id
        self.reg_name = reg_name
        self.data_type = data_type
    async def init(self):
        self._id, self.id_updated = await getset_port_id(
            self.node_id,
            self.callback,
            def_id=self.def_id,
            reg_name=self.reg_name,
            data_type=self.data_type
        )
    async def callback(self, data, _):
        self.data = data
    def get_id_string(self):
        if not self.id_updated:
            string =  str(self._id)
        else:
            toggle = bool(int(time.time() * 1000) % 1000 > 500)
            string =  f"{Colors.OKCYAN}{self._id}{Colors.ENDC}" if toggle else str(self._id)
        return string

class CircuitStatusTemperatureSub(BaseSubscriber):
    def __init__(self, node_id, def_id=2102, reg="uavcan.pub.crct.temp.id") -> None:
        super().__init__(node_id, def_id, reg, uavcan.si.sample.temperature.Scalar_1_0)
    def print_data(self):
        print("CircuitStatus:")
        if self.data is not None:
            kelvin = self.data.kelvin
            celcius = kelvin - 273
        else:
            kelvin = 0
            celcius = 0
        print(f"- crct.temp ({self.get_id_string()}): {kelvin} Kelvin ({celcius} Celcius)")

class GpsSatsSub(BaseSubscriber):
    def __init__(self, node_id, def_id=2001, reg="uavcan.pub.zubax.gps.sats.id") -> None:
        super().__init__(node_id, def_id, reg, uavcan.primitive.scalar.Integer16_1_0)
    def print_data(self):
        print(f"GNSS:")
        value = self.data.value if self.data is not None else None
        if value == 0:
            value = Colorizer.header(value) 
        print(f"- sats ({self.get_id_string()}): {value}")
        print(f"- lat:")
        print(f"- lon:")

class GpsTimeUtcSub(BaseSubscriber):
    def __init__(self, node_id, def_id=2002, reg="uavcan.pub.gps.time_utc.id") -> None:
        super().__init__(node_id, def_id, reg, uavcan.time.SynchronizedTimestamp_1_0)
    def print_data(self):
        seconds = int(self.data.microsecond / 1000000) if self.data is not None else 0
        print(f"- time_utc ({self.get_id_string()}): {seconds} ({datetime.datetime.fromtimestamp(seconds)})")

class MagnetometerSub(BaseSubscriber):
    def __init__(self, node_id, def_id=2000, reg="uavcan.pub.zubax.mag.id") -> None:
        super().__init__(node_id, def_id, reg, uavcan.si.sample.magnetic_field_strength.Vector3_1_1)
        self.data = None
    def print_data(self):
        if self.data is not None:
            print(f"Magnetometer zubax.mag ({self.get_id_string()}):")
            mag_field = self.data.ampere_per_meter.tolist()
            print(f"- norm: {np.sqrt(np.sum(np.array(mag_field)**2)):.3f} Amper/meter")
            print(f"- x: {mag_field[0]:.3f} Amper/meter")
            print(f"- y: {mag_field[1]:.3f} Amper/meter")
            print(f"- z: {mag_field[1]:.3f} Amper/meter")
        else:
            print(f"Magnetometer ({self.get_id_string()}) : {Colors.WARNING}NO DATA{Colors.ENDC}")

class BaroPressureSub(BaseSubscriber):
    def __init__(self, node_id, def_id=2100, reg="uavcan.pub.zubax.baro.press.id") -> None:
        super().__init__(node_id, def_id, reg, uavcan.si.sample.pressure.Scalar_1_0)
    def print_data(self):
        print("Barometer:")
        value = self.data.pascal if self.data is not None else 0.0
        print(f"- zubax.baro.press ({self.get_id_string()}): {value:.2f} Pascal")

class BaroTemperatureSub(BaseSubscriber):
    def __init__(self, node_id, def_id=2101, reg="uavcan.pub.zubax.baro.temp.id") -> None:
        super().__init__(node_id, def_id, reg, uavcan.si.sample.temperature.Scalar_1_0)
    def print_data(self):
        print(f"- zubax.baro.temp ({self.get_id_string()}): {self.data.kelvin:.2f} Kelvin")

class BaseMonitor:
    def __init__(self) -> None:
        pass

    @staticmethod
    def get_latest_sw_version() -> int:
        return 0

    @staticmethod
    def get_vssc_meaning(vssc : int) -> str:
        return f"{vssc} (meaning unknown)"


class GpsMagBaroMonitor(BaseMonitor):
    def __init__(self, node_id) -> None:
        self.node_id = node_id

        self.subs = [
            GpsSatsSub(node_id),
            GpsTimeUtcSub(node_id),
            MagnetometerSub(node_id),
            BaroPressureSub(node_id),
            BaroTemperatureSub(node_id)
        ]

    async def init(self):
        for sub in self.subs:
            await sub.init()

    async def process(self):
        for sub in self.subs:
            sub.print_data()

    @staticmethod
    def get_latest_sw_version() -> int:
        return 0xc78d47c3c9744f55

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
    def __init__(self, node_id) -> None:
        self.node_id = node_id

        self.subs = [
            CircuitStatusTemperatureSub(node_id),
        ]

        self.pubs = [
            HighColorPub(node_id),
        ]

    async def init(self):
        for pub in self.pubs:
            await pub.init()

        for sub in self.subs:
            await sub.init()

    async def process(self):
        for pub in self.pubs:
            await pub.process_publisher()
        for sub in self.subs:
            sub.print_data()

class RLConfigurator:
    def __init__(self) -> None:
        self.node_id = None
        self.heartbeat = uavcan.node.Heartbeat_1_0()

    async def main(self):
        cyphal_node = await CyphalTools.get_node()
        heartbeat_sub = cyphal_node.make_subscriber(uavcan.node.Heartbeat_1_0)
        heartbeat_sub.receive_in_background(self._heartbeat_callback)

        info, name, node_monitor = await self._find_node()

        await asyncio.sleep(0.1)
        while True:
            os.system('clear')
            print("RaccoonLab monitor")
            print("Node info:")
            print(f"- Name: {name}")

            print(f"- SW: ", end='')
            sw_version_string = f"v{info['sw_version'][0]}.{info['sw_version'][1]}_{hex(info['git_hash'])[2:]}"
            if info['git_hash'] == node_monitor.get_latest_sw_version():
                print(f"{sw_version_string} (latest)")
            else:
                print(f"{Colors.FAIL}{sw_version_string} (need update){Colors.ENDC}")

            hw_version_string = f"v{info['hw_version'][0]}.{info['hw_version'][1]}"
            print(f"- HW: {hw_version_string}")


            print(f"- ID: {self.node_id}")
            print(f"- Health: {RLConfigurator._health_to_string(self.heartbeat.health.value)}")
            print(f"- Mode: {RLConfigurator._mode_to_string(self.heartbeat.mode.value)}")
            print(f"- VSSC: {node_monitor.get_vssc_meaning(self.heartbeat.vendor_specific_status_code)}")

            print(f"- UID: {info['uid']}")
            print(f"- Uptime: {self.heartbeat.uptime}")
            await node_monitor.process()
            await asyncio.sleep(0.1)

    async def _find_node(self) -> BaseMonitor:
        # 1. Define node ID
        self.node_id = await CyphalTools.find_online_node(timeout=5.0)
        while self.node_id is None:
            self.node_id = await CyphalTools.find_online_node(timeout=5.0)
        print(f"Node with ID={self.node_id} has been found.")

        # 2. Define node name
        info = await CyphalTools.get_tested_node_info()
        name = info['name']
        if name == 'co.raccoonlab.gps_mag_baro':
            print(f"Node `{name}` has been found.")
            node = GpsMagBaroMonitor(self.node_id)
        elif name == 'co.raccoonlab.lights':
            print(f"Node `{name}` has been found.")
            node = UavLightsMonitor(self.node_id)
        else:
            print(f"Unknown node `{name}` has been found. Exit")
            sys.exit(0)

        await node.init()
        return info, name, node

    async def _heartbeat_callback(self, data, transfer_from):
        if self.node_id == transfer_from.source_node_id:
            self.heartbeat = data

    @staticmethod
    def _health_to_string(value : int) -> str:
        assert isinstance(value, int)
        mapping = {
            0 : "NOMINAL (0)",
            1 : f"{Colors.HEADER}ADVISORY (1){Colors.ENDC}",
            2 : f"{Colors.WARNING}CAUTION (2){Colors.ENDC}",
            3 : f"{Colors.FAIL}WARNING (3){Colors.ENDC}",
        }
        assert value in mapping
        return mapping[value]

    @staticmethod
    def _mode_to_string(value : int) -> str:
        assert isinstance(value, int)
        mapping = {
            0: "OPERATIONAL",
            1: Colorizer.okcyan("INITIALIZATION"),
            2: Colorizer.header("MAINTENANCE"),
            3: Colorizer.warning("SOFTWARE_UPDATE"),
        }

        return mapping[value]

if __name__ == "__main__":
    rl_configurator = RLConfigurator()
    try:
        asyncio.run(rl_configurator.main())
    except KeyboardInterrupt:
        print("Aborted by KeyboardInterrupt.")
