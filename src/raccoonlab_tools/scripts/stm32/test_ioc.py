#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
import sys
import yaml
import argparse

RL_V2 = {
    'PA0': 'ADC_VIN',
    'PA1': 'ADC_5V',
    'PA4': 'INT_RGB_LED_BLUE',
    'PA8': 'INT_RGB_LED_GREEN',
    'PA15': 'INT_RGB_LED_RED',
    'PB1': 'ADC_VERSION'
}

RL_V3 = {
    'PA0': 'ADC_VIN',
    'PA1': 'ADC_5V',
    'PA6': 'ADC_CURRENT',
    'PA7': 'ADC_VERSION',
    'PC13': 'INTERNAL_LED_RED',
    'PC14': 'INTERNAL_LED_GREEN',
    'PC15': 'INTERNAL_LED_BLUE',
    'PA15': 'CAN1_TERMINATOR',
    'PB15': 'CAN2_TERMINATOR'
}

VERSION_TO_CONFIG = {
    "v2" : RL_V2,
    "v3" : RL_V3,
}

def find_unconfigured_pins(required_pinout : dict, ioc_lines : list) -> dict:
    assert isinstance(required_pinout, dict)
    assert isinstance(ioc_lines, list)

    unconfigured_pins = {pin: None for pin in required_pinout}

    for ioc_line in ioc_lines:
        ioc_line = ioc_line.rstrip()
        for pin_name in required_pinout:
            if ioc_line.startswith(pin_name) and ioc_line.endswith(required_pinout[pin_name]):
                del unconfigured_pins[pin_name]

    return unconfigured_pins

def main():
    parser = argparse.ArgumentParser(description="Test .ioc file")
    parser.add_argument("pinout_config", help="Path to the required config file")
    parser.add_argument("ioc_file_path", help="Path to the actual IOC file")
    args = parser.parse_args()

    if args.pinout_config in VERSION_TO_CONFIG:
        required_pinout = VERSION_TO_CONFIG[args.pinout_config]
    else:
        with open(args.pinout_config, 'r', encoding='UTF-8') as pinout_config_fd:
            required_pinout = yaml.safe_load(pinout_config_fd)

    with open(args.ioc_file_path, 'r', encoding='UTF-8') as ioc_fd:
        ioc_lines = ioc_fd.readlines()

    not_configured_pinout = find_unconfigured_pins(required_pinout, ioc_lines)
    if not_configured_pinout:
        error_msg = ""
        for pin in not_configured_pinout:
            error_msg += f"- {pin:4} should be {required_pinout[pin]}\n"
        sys.exit(f"There are not configured pins:\n{error_msg}")
    else:
        print(f"{args.ioc_file_path} is fine.")

if __name__ == "__main__":
    main()
