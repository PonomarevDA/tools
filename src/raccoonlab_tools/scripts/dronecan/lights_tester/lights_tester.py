#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Anastasiia Stepanova.
# Author: Anastasiia Stepanova <asiiapine@gmail.com>

import argparse
import dronecan
from dronecan import uavcan
import time


class RGB565_color:
    red: int  #: uint5
    green: int  # :uint6
    blue: int  #: uint5

    def __init__(self, red=0, green=0, blue=0) -> None:
        self.red = red
        self.green = green
        self.blue = blue

    def reset(self) -> None:
        self.red = 0
        self.green = 0
        self.blue = 0

    def change(self, incrementor=[1, 1, 1]) -> None:
        self.red += incrementor[0]
        self.green += incrementor[1]
        self.blue += incrementor[2]
        if self.red == 32 or self.green == 64 or self.blue == 32:
            print("reset", self.red)
            self.reset()

    @property
    def values(self):
        self.change()
        return self.red, self.green, self.blue


class LightsCommander:

    colors_dict = {
                   "red": RGB565_color(red=31),
                   "red_low": RGB565_color(red=10),
                   "green": RGB565_color(green=63),
                   "green_low": RGB565_color(green=31),
                   "blue": RGB565_color(blue=31),
                   "blue_low": RGB565_color(blue=10),
                   "white": RGB565_color(red=31, green=63, blue=31),
                   "white_low": RGB565_color(red=10, green=31, blue=10),
                   "off": RGB565_color()
                   }
    
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
        self.rgb = RGB565_color()
        self.color = uavcan.equipment.indication.RGB565(
            red=self.rgb.red, green=self.rgb.green, blue=self.rgb.blue
        )
        self.commands = uavcan.equipment.indication.SingleLightCommand(
            light_id=1, color=self.color
        )
        self.light_command_msg = uavcan.equipment.indication.LightsCommand(
            commands=[self.commands],
            number_of_commands=1,
            model_name="simulated_light_commander",
        )
        self.node_status_msg = uavcan.equipment.indication.LightsCommand()

        self.node.add_handler(uavcan.protocol.NodeStatus, self._node_status_callback)

        self.online_nodes = set()

        if colors_dict is not None:
            self.colors_dict = colors_dict

        self.color_names = list(self.colors_dict.keys())

    def spin(self):
        while True:
            i = int(time.time() % len(self.color_names))
            
            color_name = list(self.colors_dict.keys())[i]
            color = self.colors_dict[color_name]

            self.color = uavcan.equipment.indication.RGB565(red=color.red, green=color.green, blue=color.blue)

            self.commands = uavcan.equipment.indication.SingleLightCommand(
                light_id=1, color=self.color
            )

            self.node.spin(0.5)
            if len(self.online_nodes) >= 1:
                self.light_command_msg = uavcan.equipment.indication.LightsCommand(
                    commands=[self.commands],
                    number_of_commands=1,
                    model_name="simulated_light_commander",
                )
                self.node.broadcast(self.light_command_msg)
                print("Pub LightsCommand")
            else:
                print("There is no any online node yet...")

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
