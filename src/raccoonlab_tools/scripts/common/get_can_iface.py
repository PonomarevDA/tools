#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

from raccoonlab_tools.common.device_manager import DeviceManager

def main():
    """Example of print:
    - slcan:/dev/ttyACM0@1000000
    - socketcan:slcan0
    """
    try:
        transport = DeviceManager.get_transport()
    except Exception:
        return

    if transport.startswith("slcan"):
        print(f"socketcan:{transport}")
    else:
        print(f"slcan:{transport}@1000000")

if __name__ == "__main__":
    main()
