#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
import yaml
import dronecan
import argparse
from raccoonlab_tools.dronecan.utils import Parameter, \
                                            ParametersInterface, \
                                            NodeFinder, \
                                            NodeCommander

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()

    node = dronecan.make_node('slcan:/dev/ttyACM0', node_id=100, bitrate=1000000, baudrate=1000000)
    target_node_id = NodeFinder(node).find_online_node()
    params_interface = ParametersInterface(node=node, target_node_id=target_node_id)
    commander = NodeCommander(node=node, target_node_id=target_node_id)

    with open(args.config, "r", encoding='UTF-8') as stream:
        params = yaml.safe_load(stream)['params']
        for name in params:
            desired_param = Parameter(name=name, value=params[name])
            param_after_change = params_interface.set(desired_param)
            print(param_after_change)

        print(commander.store_persistent_states())
        print(commander.restart())

if __name__ =="__main__":
    main()
