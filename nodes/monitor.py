#!/usr/bin/env python3
import os
import sys
import time
import datetime
import asyncio
import pathlib
import numpy as np

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

def mode_value_to_string(value):
    mapping = {
        0 : "OPERATIONAL",
        1 : f"{Colors.OKCYAN}INITIALIZATION{Colors.ENDC}",
        2 : f"{Colors.HEADER}MAINTENANCE{Colors.ENDC}",
        3 : f"{Colors.WARNING}SOFTWARE_UPDATE{Colors.ENDC}",
    }
    return mapping[value]

def health_value_to_string(value):
    mapping = {
        0 : "NOMINAL (0)",
        1 : f"{Colors.HEADER}ADVISORY (1){Colors.ENDC}",
        2 : f"{Colors.WARNING}CAUTION (2){Colors.ENDC}",
        3 : f"{Colors.FAIL}WARNING (3){Colors.ENDC}",
    }
    return mapping[value]

def vssc_value_to_string(value):
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
        if value & np.left_shift(1, number):
            errors.append(bit_meaning)

    if len(errors) > 0:
        string = ", ".join(str(error) for error in errors)
        string = f"{Colors.WARNING}{value}: ({string}){Colors.ENDC}"
    else:
        string = f"{value}"
    return string

async def getset_port_id(node_id, callback, def_id, reg_name, data_type):
    assert isinstance(def_id, int)
    print(node_id, def_id, reg_name, data_type)
    cyphal_node = await CyphalTools.get_node()
    access_client = cyphal_node.make_client(uavcan.register.Access_1_0, node_id)

    id = await CyphalTools.get_port_id_reg_value(node_id, reg_name)
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

class BaseTopic:
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

class GpsSatsTopic(BaseTopic):
    def __init__(self, node_id, def_id=2001, reg="uavcan.pub.zubax.gps.sats.id") -> None:
        super().__init__(node_id, def_id, reg, uavcan.primitive.scalar.Integer16_1_0)
    def print_data(self):
        print(f"GNSS:")
        value = self.data.value if self.data is not None else None
        print(f"- sats ({self.get_id_string()}): {value}")
        print(f"- lat:")
        print(f"- lon:")

class GpsTimeUtcTopic(BaseTopic):
    def __init__(self, node_id, def_id=2002, reg="uavcan.pub.gps.time_utc.id") -> None:
        super().__init__(node_id, def_id, reg, uavcan.time.SynchronizedTimestamp_1_0)
    def print_data(self):
        seconds = int(self.data.microsecond / 1000000) if self.data is not None else 0
        print(f"- time_utc ({self.get_id_string()}): {seconds} ({datetime.datetime.fromtimestamp(seconds)})")

class MagnetometerTopic(BaseTopic):
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

class BaroPressureTopic(BaseTopic):
    def __init__(self, node_id, def_id=2100, reg="uavcan.pub.zubax.baro.press.id") -> None:
        super().__init__(node_id, def_id, reg, uavcan.si.sample.pressure.Scalar_1_0)
    def print_data(self):
        print("Barometer:")
        value = self.data.pascal if self.data is not None else 0.0
        print(f"- zubax.baro.press ({self.get_id_string()}): {value:.2f} Pascal")

class BaroTemperatureTopic(BaseTopic):
    def __init__(self, node_id, def_id=2101, reg="uavcan.pub.zubax.baro.temp.id") -> None:
        super().__init__(node_id, def_id, reg, uavcan.si.sample.temperature.Scalar_1_0)
    def print_data(self):
        print(f"- zubax.baro.temp ({self.get_id_string()}): {self.data.kelvin:.2f} Kelvin")


class GpsMagBaroMonitor:
    def __init__(self, node_id) -> None:
        self.node_id = node_id

        self.topics = [GpsSatsTopic(node_id),
                       GpsTimeUtcTopic(node_id),
                       MagnetometerTopic(node_id),
                       BaroPressureTopic(node_id),
                       BaroTemperatureTopic(node_id)]

    async def init(self):
        for topic in self.topics:
            await topic.init()

    def print_text(self):
        for topic in self.topics:
            topic.print_data()

class RaccoonLabConfigurator:
    def __init__(self) -> None:
        self.node_id = None
        self.heartbeat = uavcan.node.Heartbeat_1_0()

    async def main(self):
        cyphal_node = await CyphalTools.get_node()
        heartbeat_sub = cyphal_node.make_subscriber(uavcan.node.Heartbeat_1_0)
        heartbeat_sub.receive_in_background(self.heartbeat_callback)

        info, name, node = await self.find_node()

        await asyncio.sleep(0.1)
        while True:
            os.system('clear')
            print("RaccoonLab monitor")
            print("Node info:")
            print(f"- Name: {name}")

            print(f"- SW: ", end='')
            sw_version_string = f"v{info['sw_version'][0]}.{info['sw_version'][1]}_{hex(info['git_hash'])[2:]}"
            if info['git_hash'] == 0x2369cc5265ad8492:
                print(f"{sw_version_string} (latest)")
            else:
                print(f"{Colors.FAIL}{sw_version_string} (need update){Colors.ENDC}")

            hw_version_string = f"v{info['hw_version'][0]}.{info['hw_version'][1]}"
            print(f"- HW: {hw_version_string}")


            print(f"- ID: {self.node_id}")
            print(f"- Health: {health_value_to_string(self.heartbeat.health.value)}")
            print(f"- Mode: {mode_value_to_string(self.heartbeat.mode.value)}")
            print(f"- VSSC: {vssc_value_to_string(self.heartbeat.vendor_specific_status_code)}")

            print(f"- UID: {info['uid']}")
            print(f"- Uptime: {self.heartbeat.uptime}")
            node.print_text()
            await asyncio.sleep(0.1)

    async def find_node(self):
        # 1. Define node ID
        self.node_id = await CyphalTools.find_online_node(timeout=5.0)
        while self.node_id is None:
            self.node_id = await CyphalTools.find_online_node(timeout=5.0)
        print(f"Node with ID={self.node_id} has been found.")

        # 2. Define node name
        info = await CyphalTools.get_tested_node_info()
        name = info['name']
        if name == 'co.raccoonlab.gps_mag_baro':
            print(f"Well-known node `{name}` has been found.")
        else:
            print(f"Unknown node `{name}` has been found. Exit")
            sys.exit(0)

        node = GpsMagBaroMonitor(self.node_id)
        await node.init()

        return info, name, node

    async def heartbeat_callback(self, data, transfer_from):
        if self.node_id == transfer_from.source_node_id:
            self.heartbeat = data

if __name__ == "__main__":
    rl_configurator = RaccoonLabConfigurator()
    try:
        asyncio.run(rl_configurator.main())
    except KeyboardInterrupt:
        print("Aborted by KeyboardInterrupt.")
