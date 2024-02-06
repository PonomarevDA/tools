#!/usr/bin/env python
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import argparse
import yaml
from raccoonlab_tools.common.st_link_linux import StlinkLinux
from raccoonlab_tools.common.firmware import get_firmware

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()

    with open(args.config, "r", encoding='UTF-8') as stream:
        config = yaml.safe_load(stream)
        binary_path = get_firmware(config['metadata']['link'])
        StlinkLinux.upload_firmware(binary_path)

if __name__ == '__main__':
    main()
