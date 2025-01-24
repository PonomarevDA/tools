#!/usr/bin/env python
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import argparse
import yaml
from raccoonlab_tools.common.firmware_manager import FirmwareManager
from raccoonlab_tools.common.device_manager import DeviceManager
import os

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--config', help='Path to .yaml config file')
    group.add_argument('--binary', help='Path to .bin binary file')
    args = parser.parse_args()

    if args.config:
        with open(args.config, "r", encoding='UTF-8') as stream:
            config = yaml.safe_load(stream)
            binary_path = FirmwareManager.get_firmware(config['metadata']['link'])
    elif args.binary:
        binary_path = args.binary

    if (os.path.exists("/proc/device-tree/model")):
        print("I'm rpi")
    else:
        # Just to check that the programmer is avaliable
        DeviceManager.get_programmer()

    FirmwareManager.upload_firmware(binary_path)

if __name__ == '__main__':
    main()
