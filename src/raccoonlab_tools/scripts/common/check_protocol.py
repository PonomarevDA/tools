#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

from raccoonlab_tools.common.protocol_parser import CanProtocolParser
from raccoonlab_tools.common.device_manager import DeviceManager

def main():
    sniffer = DeviceManager.get_transport(verbose=True)
    CanProtocolParser.find_protocol(sniffer, verbose=True)

if __name__ == "__main__":
    main()
