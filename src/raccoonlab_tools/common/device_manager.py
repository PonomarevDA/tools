#!/usr/bin/env python3
import sys
from dataclasses import dataclass
import serial.tools.list_ports

@dataclass
class UsbDevice:
    vendor: str
    desc: str
    hwid: str
    port: str = None

KNOWN_SNIFFERS = [
    UsbDevice("RaccoonLab", "STM32 STLink - ST-Link VCP Ctrl",              "USB VID:PID=0483:374B"),
    UsbDevice("Zubax",      "Zubax Babel",                                  "USB VID:PID=1D50:60C7"),
]

KNOWN_PROGRAMMERS = [
    UsbDevice("RaccoonLab", "STM32 STLink - ST-Link VCP Ctrl",              "USB VID:PID=0483:374B"),
    UsbDevice("Zubax",      "Black Magic Probe - Black Magic GDB Server",   "USB VID:PID=1D50:6018"),
]

class DeviceManager:
    @staticmethod
    def get_sniffer(verbose=False):
        sniffers = DeviceManager().find_sniffers(verbose)
        if len(sniffers) == 0:
            raise Exception("[ERROR] CAN-sniffer has not been automatically found.")
        return sniffers[0].port

    @staticmethod
    def find_sniffers(verbose=False) -> list:
        sniffers = []
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            for known_sniffer in KNOWN_SNIFFERS:
                if desc == known_sniffer.desc or hwid.startswith(known_sniffer.hwid):
                    known_sniffer.port = port
                    sniffers.append(known_sniffer)
                    break

        if len(sniffers) == 0:
            print("[ERROR] CAN-sniffer has not been automatically found.")
        elif verbose:
            print("Online CAN-sniffers:")
            for sniffer in sniffers:
                print(f"- {sniffer}")

        return sniffers

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


if __name__ == "__main__":
    DeviceManager.find_sniffers(verbose=True)
    DeviceManager.find_programmers(verbose=True)
