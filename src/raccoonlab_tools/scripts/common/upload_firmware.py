#!/usr/bin/env python
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import argparse
import yaml
from raccoonlab_tools.common.firmware_manager import FirmwareManager

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()

    with open(args.config, "r", encoding='UTF-8') as stream:
        config = yaml.safe_load(stream)
        binary_path = FirmwareManager.get_firmware(config['metadata']['link'])
        FirmwareManager.upload_firmware(binary_path)

if __name__ == '__main__':
    main()
