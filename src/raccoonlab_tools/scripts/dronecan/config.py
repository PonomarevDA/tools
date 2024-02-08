#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
import argparse
import yaml
import dronecan
from raccoonlab_tools.dronecan.utils import Parameter, \
                                            ParametersInterface, \
                                            NodeFinder, \
                                            NodeCommander
from raccoonlab_tools.common.firmware_manager import FirmwareManager
from raccoonlab_tools.common.device_manager import DeviceManager


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, help="path to yaml file")
    parser.add_argument('--can-transport', default=None, help=("Auto detect by default. Options: "
                                                               "slcan:/dev/ttyACM0, "
                                                               "socketcan:slcan0.")
    )
    args = parser.parse_args()

    if args.can_transport is None:
        device_manager = DeviceManager()
        sniffer_port = device_manager.get_all_online_sniffers()[0].port
        can_transport = f'slcan:{sniffer_port}'
    else:
        can_transport = args.can_transport

    with open(args.config, "r", encoding='UTF-8') as stream:
        config = yaml.safe_load(stream)

        FirmwareManager.upload_firmware(FirmwareManager.get_firmware(config['metadata']['link']))

        params = config['params']
        node = dronecan.make_node(can_transport, node_id=100, bitrate=1000000, baudrate=1000000)
        target_node_id = NodeFinder(node).find_online_node()
        params_interface = ParametersInterface(node=node, target_node_id=target_node_id)
        commander = NodeCommander(node=node, target_node_id=target_node_id)
        for name in params:
            desired_param = Parameter(name=name, value=params[name])
            param_after_change = params_interface.set(desired_param)
            print(param_after_change)

        print(f"Save persistent parameters: {commander.store_persistent_states()}")
        print(f"Reboot: {commander.restart()}")

if __name__ =="__main__":
    main()
