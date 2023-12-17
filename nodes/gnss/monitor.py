#!/usr/bin/env python3
import os
import sys
import datetime
import asyncio
import pathlib
import numpy

repo_dir = pathlib.Path(__file__).resolve().parent.parent.parent
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
        if value & numpy.left_shift(1, number):
            errors.append(bit_meaning)

    if len(errors) > 0:
        string = "".join(str(error) for error in errors)
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
    if id == 65535:
        set_request = uavcan.register.Access_1_0.Request()
        set_request.name.name = reg_name
        set_request.value.natural16 = uavcan.primitive.array.Natural16_1_0(def_id)
        await access_client.call(set_request)
    id = def_id
    assert isinstance(id, int), reg_name
    mag_sub = cyphal_node.make_subscriber(data_type, id)
    mag_sub.receive_in_background(callback)
    access_client.close()

    return id

class GnssMonitor:
    def __init__(self) -> None:
        self.node_id = None
        self.heartbeat = uavcan.node.Heartbeat_1_0()
        self.baro_press_pascal = 0.0
        self.baro_temp_kelvin = 0.0
        self.mag_data = [-42.0, -42.0, -42.0]
        self.gnss_sats = 0
        self.gnss_time_utc = 0

    async def main(self):
        cyphal_node = await CyphalTools.get_node()
        while self.node_id is None:
            self.node_id = await CyphalTools.find_online_node()
        name = await CyphalTools.get_tested_node_name()

        heartbeat_sub = cyphal_node.make_subscriber(uavcan.node.Heartbeat_1_0)
        heartbeat_sub.receive_in_background(self.heartbeat_callback)

        # Barometer
        baro_press_id = await getset_port_id(self.node_id,
                                             self.baro_press_callback,
                                             def_id=2100,
                                             reg_name="uavcan.pub.zubax.baro.press.id",
                                             data_type=uavcan.si.sample.pressure.Scalar_1_0)
        baro_temp_id = await getset_port_id(self.node_id,
                                            self.baro_temp_callback,
                                            def_id=2101,
                                            reg_name="uavcan.pub.zubax.baro.temp.id",
                                            data_type=uavcan.si.sample.temperature.Scalar_1_0)
        await asyncio.sleep(0.1)

        # Magnetometer
        mag_id = await getset_port_id(self.node_id,
                                      self.mag_callback,
                                      def_id=2000,
                                      reg_name="uavcan.pub.zubax.mag.id",
                                      data_type=uavcan.si.sample.magnetic_field_strength.Vector3_1_1)
        await asyncio.sleep(0.1)

        # GNSS
        gnss_sats_id = await getset_port_id(self.node_id,
                                            self.gnss_sats_callback,
                                            def_id=2001,
                                            reg_name="uavcan.pub.zubax.gps.sats.id",
                                            data_type=uavcan.primitive.scalar.Integer16_1_0)
        time_utc_id = await getset_port_id(self.node_id,
                                           self.time_utc_callback,
                                           def_id=2002,
                                           reg_name="uavcan.pub.gps.time_utc.id",
                                           data_type=uavcan.time.SynchronizedTimestamp_1_0)
        await asyncio.sleep(0.1)

        while True:
            os.system('clear')
            print("RaccoonLab GNSS monitor")
            print("Node info:")
            print(f"- Name: {name}")
            print(f"- ID: {self.node_id}")
            print(f"- Health: {health_value_to_string(self.heartbeat.health.value)}")
            print(f"- Mode: {mode_value_to_string(self.heartbeat.mode.value)}")
            print(f"- VSSC: {vssc_value_to_string(self.heartbeat.vendor_specific_status_code)}")

            print("GNSS:")
            print(f"- sats ({gnss_sats_id}): {self.gnss_sats}")
            print(f"- time_utc ({time_utc_id}): {self.gnss_time_utc} ({datetime.datetime.fromtimestamp(self.gnss_time_utc)})")

            print("Barometer:")
            print(f"- pressure ({baro_press_id}): {self.baro_press_pascal:.2f} Pascal")
            print(f"- temperature ({baro_temp_id}): {self.baro_temp_kelvin:.2f} Kelvin")

            print(f"Magnetometer: ({mag_id}) : {self.mag_data[0]:.3f} {self.mag_data[1]:.3f} {self.mag_data[2]:.3f} Amper/meter")

            await asyncio.sleep(0.1)

    async def baro_press_callback(self, data, _):
        self.baro_press_pascal = data.pascal

    async def baro_temp_callback(self, data, _):
        self.baro_temp_kelvin = data.kelvin

    async def mag_callback(self, data, _):
        self.mag_data = data.ampere_per_meter.tolist()

    async def gnss_sats_callback(self, data, _):
        self.gnss_sats = data.value

    async def time_utc_callback(self, data, _):
        self.gnss_time_utc = int(data.microsecond / 1000000)

    async def heartbeat_callback(self, data, transfer_from):
        if self.node_id == transfer_from.source_node_id:
            self.heartbeat = data

if __name__ == "__main__":
    gnss_monitor = GnssMonitor()
    asyncio.run(gnss_monitor.main())
