#!/usr/bin/env python3
from dataclasses import dataclass
import serial.tools.list_ports
import netifaces
import platform

@dataclass
class CanInterface:
    vendor: str = "Unknown"
    desc: str = "Unknown"
    hwid: str = "Unknown"
    port: str = None

KNOWN_SNIFFERS = [
    CanInterface("RaccoonLab", "STM32 STLink - ST-Link VCP Ctrl",              "USB VID:PID=0483:374B"),
    CanInterface("Zubax",      "Zubax Babel",                                  "USB VID:PID=1D50:60C7"),
]

KNOWN_PROGRAMMERS = [
    CanInterface("RaccoonLab", "STM32 STLink - ST-Link VCP Ctrl",              "USB VID:PID=0483:374B"),
    CanInterface("Zubax",      "Black Magic Probe - Black Magic GDB Server",   "USB VID:PID=1D50:6018"),
]

class DeviceManager:
    @staticmethod
    def find_transports(verbose=False) -> list:
        transports = []

        system = platform.system()
        if system == "Linux":
            for interface in netifaces.interfaces():
                if interface.startswith("slcan"):
                    transports.append(CanInterface(port=interface))

        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            for known_sniffer in KNOWN_SNIFFERS:
                if desc == known_sniffer.desc or hwid.startswith(known_sniffer.hwid):
                    known_sniffer.port = port
                    transports.append(known_sniffer)
                    break

        if len(transports) == 0:
            print("[ERROR] Appropriate transport has not been automatically found.")
        elif verbose:
            print("Avaliable CAN-transports:")
            for transport in transports:
                print(f"- {transport}")

        return transports

    @staticmethod
    def get_transport(verbose=False) -> str:
        """ Return examples: ["/dev/ttyACM0", "COM16", "slcan0"] """
        transports = DeviceManager.find_transports(verbose)
        if len(transports) == 0:
            raise Exception("[ERROR] CAN-sniffer has not been automatically found.")
        return transports[0].port

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
            print("[ERROR] STM32-programmer has not been automatically found.")
        elif verbose:
            print("Online STM32-programmers:")
            for programmer in programmers:
                print(f"- {programmer}")

        return programmers

    @staticmethod
    def get_programmer(verbose=False):
        programmers = DeviceManager().find_programmers(verbose)
        if len(programmers) == 0:
            raise Exception("[ERROR] STM32-Programmer has not been automatically found.")
        return programmers[0].port

if __name__ == "__main__":
    DeviceManager.find_transports(verbose=True)
    DeviceManager.find_programmers(verbose=True)
