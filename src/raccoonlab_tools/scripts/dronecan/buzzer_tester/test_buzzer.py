#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Anastasiia Stepanova.
# Author: Anastasiia Stepanova <asiiapine@gmail.com>

import argparse
import random
import dronecan
from dronecan import uavcan
import time


class LightsCommander:
    
    def __init__(self, port: str, node_id: int=100, bitrate: int=1000000, baudrate: int=1000000, colors_dict: dict=None) -> None:
        self.node = dronecan.make_node(
            port,
            node_id=node_id,
            bitrate=bitrate,
            baudrate=baudrate,
            mode=dronecan.uavcan.protocol.NodeStatus().MODE_OPERATIONAL,
        )

        self.timer = time.time()

        # the first command - turn off the lights
        self.frequency = random.randrange(1, 1000)
        self.duration = random.randrange(1, 1000)
        self.command = uavcan.equipment.indication.BeepCommand(
            frequency=self.frequency, duration=self.duration
        )

        self.node.add_handler(uavcan.protocol.NodeStatus, self._node_status_callback)

        self.online_nodes = set()

    def spin(self):
        while True:
            self.frequency = random.randrange(1, 1000)
            self.duration = random.randrange(1, 1000)
            self.command = uavcan.equipment.indication.BeepCommand(
            frequency=self.frequency, duration=self.duration
            )
            self.node.spin(0.5)
            if len(self.online_nodes) >= 1:
                self.node.broadcast(self.command)
                print("Pub BeepCommand")
            else:
                print("There is no any online node yet...")
            time.sleep(1)

    def _node_status_callback(self, msg):
        self.online_nodes.add(msg.transfer.source_node_id)
        print(f"Receive NodeStatus from node {msg.transfer.source_node_id}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulated DroneCAN LightsCommander")
    parser.add_argument(
        "port",
        type=str,
        help="CAN sniffer port. Example: slcan:/dev/ttyACM0",
        nargs="?",
        default="slcan:/dev/ttyACM0",
    )

    args = parser.parse_args()
    lights = LightsCommander(args.port)
    lights.spin()
