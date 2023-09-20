#!/usr/bin/env python3
import os
from datetime import date
import logging

import dronecan
from dronecan import uavcan


class DronecanGpsMagBaroChecker:
    def __init__(self, node):
        self._node = node

        node.add_handler(uavcan.equipment.gnss.Fix2, self._gps_callback)
        self._sats_used = None
        self._required_sats = 6

        node.add_handler(uavcan.equipment.ahrs.MagneticFieldStrength, self._mag_callback)
        self._magnetic_field_ga = None

        node.add_handler(uavcan.equipment.air_data.StaticPressure, self._static_pressure_callback)
        self._static_pressure = None

        node.add_handler(uavcan.equipment.air_data.StaticTemperature, self._static_temperature_callback)
        self._static_temperature = None

        req = uavcan.protocol.GetNodeInfo.Request()
        node.request(req, 70, self._node_info_callback)
        self.software_version = None
        self.hardware_version = None

    def is_valid(self):
        return self.is_gps_valid() and self.is_mag_valid() and self.is_baro_valid()

    def is_gps_valid(self):
        return self._sats_used is not None and self._sats_used >= self._required_sats

    def is_mag_valid(self):
        return self._magnetic_field_ga is not None

    def is_baro_valid(self):
        return self._static_pressure is not None and self._static_temperature is not None

    def get_sats_used(self):
        return self._sats_used

    def create_report(self, filename):
        current_date = date.today().strftime("%B %d, %Y")
        try:
            os.remove(filename)
        except OSError:
            pass
        with open(filename, "w", encoding="utf-8") as file:
            file.write("\nRL GNSS v2.5\n")
            file.write(f"{current_date}\n")
            file.write(f"{self.software_version}\n")
            file.write(f"{self.hardware_version}\n")

            file.write(f"GNSS: {self.is_gps_valid()}\n")
            file.write(f"Mag: {self.is_mag_valid()}\n")
            file.write(f"Baro: {self.is_baro_valid()}\n")

    def __str__(self) -> str:
        if self._sats_used is None:
            description = "Fix2 has not been published published yet."
        elif self._sats_used == 0:
            description = "Not satelites. Put the device outside with clear view of the sky."
        elif self._sats_used < self._required_sats:
            description = f"Satelites: {self._sats_used}. We need more."
        else:
            description = f"Setelites: {self._sats_used}. Goood!"
        return description

    def _node_info_callback(self, msg):
        major = msg.transfer.payload.software_version.major
        minor = msg.transfer.payload.software_version.minor
        vcs_commit = f"{msg.transfer.payload.software_version.vcs_commit:x}"

        unique_id = ""
        for first_idx in range(0, 12, 4):
            for value in msg.transfer.payload.hardware_version.unique_id[first_idx : first_idx+4]:
                unique_id += f"{int(value.value):x} "
            unique_id += "\n"

        self.software_version = f"SW: v{major}.{minor}_{vcs_commit}"
        self.hardware_version = f"UID:\n{unique_id}"

    def _gps_callback(self, msg):
        self._sats_used = msg.transfer.payload.sats_used

    def _mag_callback(self, msg):
        self._magnetic_field_ga = msg.transfer.payload.magnetic_field_ga

    def _static_pressure_callback(self, msg):
        self._static_pressure = msg.transfer.payload.static_pressure

    def _static_temperature_callback(self, msg):
        self._static_temperature = msg.transfer.payload.static_temperature


def test_dronecan_gps_mag_baro(port, filename, timeout=180):
    dronecan_node = dronecan.make_node(port, node_id=100, bitrate=1000000)
    checker = DronecanGpsMagBaroChecker(dronecan_node)
    dronecan_node.spin(0.5)
    for elapsed_time in range(0, timeout, 5):
        logging.warning("%s/%s: %s", elapsed_time, timeout, checker)
        if checker.is_gps_valid():
            break
        dronecan_node.spin(5)

    checker.create_report(filename)


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description='GNSS node checker')
    parser.add_argument("--port", default='slcan0', type=str, help="CAN sniffer port. Example: slcan0")
    parser.add_argument("--timeout", default=10, type=int, help="Waiting for satelites duration. Default 90 seconds")
    args = parser.parse_args()

    test_dronecan_gps_mag_baro(args.port, "report.txt", args.timeout)
