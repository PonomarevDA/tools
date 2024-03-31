#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
from typing import Optional
from dataclasses import dataclass
import serial.tools.list_ports
import netifaces
import platform

@dataclass
class CanInterface:
    vendor: str = "Unknown"
    desc: str = "Unknown"
    hwid: str = "Unknown"
    port: Optional[str] = None

KNOWN_SNIFFERS = [
    CanInterface("RaccoonLab", "STM32 STLink - ST-Link VCP Ctrl",              "USB VID:PID=0483:374B"),
    CanInterface("Zubax",      "Zubax Babel",                                  "USB VID:PID=1D50:60C7"),
]

KNOWN_PROGRAMMERS = [
    CanInterface("RaccoonLab", "STM32 STLink - ST-Link VCP Ctrl",              "USB VID:PID=0483:374B"),
    CanInterface("Zubax",      "Black Magic Probe - Black Magic GDB Server",   "USB VID:PID=1D50:6018"),
]

class TransportNotFoundException(Exception):
    """Exception raised when the CAN-sniffer transport is not found."""
    pass

class ProgrammerNotFoundException(Exception):
    """Exception raised when the CAN-sniffer transport is not found."""
    pass

class DeviceManager:
    @staticmethod
    def find_transports(verbose=False) -> list:
        transports = []

        system = platform.system()
        if system == "Linux":
            for interface in netifaces.interfaces():
                if interface.startswith("slcan"):
                    transports.append(CanInterface(port=interface))

        for port, desc, hwid in sorted(serial.tools.list_ports.comports()):
            for known_sniffer in KNOWN_SNIFFERS:
                if desc == known_sniffer.desc or hwid.startswith(known_sniffer.hwid):
                    known_sniffer.port = port
                    transports.append(known_sniffer)
                    break

        if verbose:
            DeviceManager._print_finding_transport_results(transports)

        return transports

    @staticmethod
    def get_device_port(verbose=False) -> str:
        """
        Find device ports and return the best one.
        Raise an exeption if it doesn't exist.
        Return examples: ["/dev/ttyACM0", "COM16", "slcan0"]
        """
        devices = DeviceManager.find_transports(verbose)
        if len(devices) == 0:
            raise TransportNotFoundException("[ERROR] CAN-transport has not been detected.")
        return devices[0].port

    @staticmethod
    def get_cyphal_can_iface() -> str:
        """
        Examples of output.
        - slcan:/dev/ttyACM0@1000000
        - socketcan:slcan0
        """
        devices = DeviceManager.find_transports()

        if len(devices) == 0:
            return ""

        best_device_port = devices[0].port
        if best_device_port.startswith("slcan"):
            can_iface_name = f"socketcan:{best_device_port}"
        else:
            can_iface_name = f"slcan:{best_device_port}@1000000"

        return can_iface_name

    @staticmethod
    def get_dronecan_can_iface() -> str:
        """
        Examples of output.
        - slcan:/dev/ttyACM0
        - slcan0
        """
        devices = DeviceManager.find_transports()

        if len(devices) == 0:
            return ""

        best_device_port = devices[0].port
        if best_device_port.startswith("slcan"):
            can_iface_name = best_device_port
        else:
            can_iface_name = f"slcan:{best_device_port}"

        return can_iface_name

    @staticmethod
    def find_programmers(verbose=True) -> list:
        programmers = []
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            for known_programmer in KNOWN_PROGRAMMERS:
                if desc == known_programmer.desc or hwid.startswith(known_programmer.hwid):
                    known_programmer.port = port
                    programmers.append(known_programmer)
                    break

        if len(programmers) == 0:
            print("[ERROR] STM32-programmer has not been detected.")
        elif verbose:
            print("Online STM32-programmers:")
            for programmer in programmers:
                print(f"- {programmer}")

        return programmers

    @staticmethod
    def get_programmer(verbose=False):
        programmers = DeviceManager().find_programmers(verbose)
        if len(programmers) == 0:
            raise ProgrammerNotFoundException("[ERROR] Programmer has not been detected.")
        return programmers[0].port

    @staticmethod
    def _print_finding_transport_results(transports : list):
        if len(transports) == 0:
            print("[ERROR] Appropriate transport has not been detected.")
        elif len(transports) == 1:
            print(f"Avaliable CAN-transports: {transports[0]}")
        else:
            print("Avaliable CAN-transports:")
            for transport in transports:
                print(f"- {transport}")

def print_cyphal_can_iface():
    print(DeviceManager.get_cyphal_can_iface())

def print_dronecan_can_iface():
    print(DeviceManager.get_dronecan_can_iface())

if __name__ == "__main__":
    DeviceManager.find_transports(verbose=True)
    DeviceManager.find_programmers(verbose=True)
    print_cyphal_can_iface()
    print_dronecan_can_iface()
