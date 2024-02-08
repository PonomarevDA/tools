#!/usr/bin/env python3
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
    def get_all_online_sniffers() -> list:
        sniffers = []
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            for known_sniffer in KNOWN_SNIFFERS:
                if desc == known_sniffer.desc or hwid.startswith(known_sniffer.hwid):
                    known_sniffer.port = port
                    sniffers.append(known_sniffer)
                    break
        return sniffers

    @staticmethod
    def get_all_online_programmers() -> list:
        programmer = []
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            for known_programmer in KNOWN_PROGRAMMERS:
                if desc == known_programmer.desc or hwid.startswith(known_programmer.hwid):
                    known_programmer.port = port
                    programmer.append(known_programmer)
                    break
        return programmer

    @staticmethod
    def print_all_online_sniffers():
        sniffers = DeviceManager.get_all_online_sniffers()
        print("Online CAN-sniffers:")
        for sniffer in sniffers:
            print(f"- {sniffer}")

    @staticmethod
    def print_all_online_programmers():
        programmers = DeviceManager.get_all_online_programmers()
        print("Online programmers:")
        for programmer in programmers:
            print(f"- {programmer}")

if __name__ == "__main__":
    DeviceManager.print_all_online_sniffers()
    DeviceManager.print_all_online_programmers()
