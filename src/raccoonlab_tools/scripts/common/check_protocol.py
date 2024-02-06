#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

from raccoonlab_tools.common.protocol_parser import CanProtocolParser
from raccoonlab_tools.common.device_manager import DeviceManager

def main():
    device_manager = DeviceManager()
    sniffer_port = device_manager.get_all_online_sniffers()[0].port
    protocol_parser = CanProtocolParser(sniffer_port)
    print(protocol_parser.get_protocol())

if __name__ == "__main__":
    main()
