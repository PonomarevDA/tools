#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
import argparse
import yaml
import dronecan
from raccoonlab_tools.dronecan.utils import Parameter, \
                                            ParametersInterface, \
                                            NodeFinder, \
                                            NodeCommander
from raccoonlab_tools.common.firmware_manager import FirmwareManager
from raccoonlab_tools.common.device_manager import DeviceManager

def upload_firmware(config : dict):
    if 'metadata' in config and 'link' in config['metadata']:
        FirmwareManager.upload_firmware(FirmwareManager.get_firmware(config['metadata']['link']))
    else:
        print("[WARN] Config file doesn't have `metadata.link` field.")

def configure_parameters(config : dict, can_transport : str):
    if 'params' not in config or config['params'] is None:
        print("[WARN] Config file doesn't have parameters. Skip the configuration.")
        return

    if can_transport is None:
        can_transport = f'slcan:{DeviceManager.get_device_port()}'

    node = dronecan.make_node(can_transport, node_id=100, bitrate=1000000, baudrate=1000000)
    target_node_id = NodeFinder(node).find_online_node()
    params_interface = ParametersInterface(node=node, target_node_id=target_node_id)
    commander = NodeCommander(node=node, target_node_id=target_node_id)
    for name in config['params']:
        desired_param = Parameter(name=name, value=config['params'][name])
        param_after_change = params_interface.set(desired_param)
        print(param_after_change)

    print(f"[INFO] Save persistent parameters: {commander.store_persistent_states()}")
    print(f"[INFO] Reboot: {commander.restart()}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, help="path to yaml file")
    parser.add_argument('--can-transport', default=None, help=("Auto detect by default. Options: "
                                                               "slcan:/dev/ttyACM0, "
                                                               "socketcan:slcan0.")
    )
    args = parser.parse_args()

    with open(args.config, "r", encoding='UTF-8') as stream:
        config = yaml.safe_load(stream)

        upload_firmware(config=config)
        configure_parameters(config=config, can_transport=args.can_transport)



if __name__ =="__main__":
    main()
