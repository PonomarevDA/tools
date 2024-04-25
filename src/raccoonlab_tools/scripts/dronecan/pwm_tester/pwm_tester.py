#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Anastasiia Stepanova.
# Author: Anastasiia Stepanova <asiiapine@gmail.com>

import argparse
import dronecan
from dronecan import uavcan
from enum import IntEnum
import time
import numpy as np
from itertools import cycle


class ParamPWMChannelId(IntEnum):
    UI_PWM = 0


class PWMArrayCommander:
    NUMBER_OF_PWM = 4
    MAX_VALUE = 1
    MIN_VALUE = -1
    NUMBER_OF_RAW_CMD_CHANNELS = 15

    def __init__(
        self,
        port: str,
        node_id: int = 100,
        bitrate: int = 1000000,
        baudrate: int = 1000000,
    ) -> None:
        self.node = dronecan.make_node(
            port,
            node_id=node_id,
            bitrate=bitrate,
            baudrate=baudrate,
            mode=dronecan.uavcan.protocol.NodeStatus().MODE_OPERATIONAL,
        )

        self.timer = time.time()
        self.node_status_msg = uavcan.equipment.actuator.Status()
        self.node.add_handler(uavcan.protocol.NodeStatus,
                               self._node_status_callback)

        self.online_nodes = set()

    def spin(self):
        values = np.linspace(start=0, stop=2 * np.pi, num=100)
        print(values.shape)
        values_iterator = cycle(values)
        for value in values_iterator:
            command_value = np.sin(value)
            command = np.ones(PWMArrayCommander.NUMBER_OF_PWM) * command_value

            expected_status_vals = []
            for i in range(PWMArrayCommander.NUMBER_OF_PWM):
                expected_status_vals.append((command[i] + 1) * 50)

            array_command = []
            for i in range(PWMArrayCommander.NUMBER_OF_PWM):
                array_command.append(
                    uavcan.equipment.actuator.Command(
                        actuator_id=i, command_value=command[i]
                    )
                )
            self.command = uavcan.equipment.actuator.ArrayCommand(
                commands=array_command
            )

            self.node.spin(0.1)
            if len(self.online_nodes) >= 1:
                self.node.broadcast(self.command)
                print("Pub ARRAYCommand")
                for i in range(PWMArrayCommander.NUMBER_OF_PWM):
                    self.expected_status_msg = uavcan.equipment.esc.Status(
                        esc_index=i,
                        power_rating_pct=int(expected_status_vals[i])
                    )
                    self.node.broadcast(self.expected_status_msg)
                    print(f"Pub Expected Status {i}")
            else:
                print("There is no any online node yet...")

    def _node_status_callback(self, msg):
        self.online_nodes.add(msg.transfer.source_node_id)
        print(f"Receive NodeStatus from node {msg.transfer.source_node_id}.")


class PWMRawCommander:
    NUMBER_OF_PWM = 4
    MAX_VALUE = 8191
    MIN_VALUE = 0
    NUMBER_OF_RAW_CMD_CHANNELS = 20

    def __init__(
        self,
        port: str,
        node_id: int = 100,
        bitrate: int = 1000000,
        baudrate: int = 1000000,
    ) -> None:
        self.node = dronecan.make_node(
            port,
            node_id=node_id,
            bitrate=bitrate,
            baudrate=baudrate,
            mode=dronecan.uavcan.protocol.NodeStatus().MODE_OPERATIONAL,
        )

        self.timer = time.time()
        self.node_status_msg = uavcan.equipment.esc.Status()

        self.node.add_handler(uavcan.protocol.NodeStatus,
                               self._node_status_callback)

        self.online_nodes = set()

    def spin(self):
        values = np.linspace(start=0, stop=2 * np.pi, num=100)
        values_iterator = cycle(values)
        for value in values_iterator:
            command_value = np.sin(value)
            command = np.ones(PWMRawCommander.NUMBER_OF_PWM) * command_value
            expected_status_vals = np.zeros(PWMRawCommander.NUMBER_OF_PWM)
            self.command = uavcan.equipment.esc.RawCommand(
                cmd=[int((val + 1) * PWMRawCommander.MAX_VALUE / 2)
                     for val in command]
            )
            for i in range(PWMRawCommander.NUMBER_OF_PWM):
                expected_status_vals[i] = 100 * (command[i] + 1)

            self.node.spin(0.5)
            if len(self.online_nodes) >= 1:
                self.node.broadcast(self.command)
                print("Pub RAWCommand")
                for i in range(PWMRawCommander.NUMBER_OF_PWM):
                    self.expected_status_msg = uavcan.equipment.esc.Status(
                        esc_index=i,
                        power_rating_pct=int(expected_status_vals[i])
                    )
                    self.node.broadcast(self.expected_status_msg)
                    print(f"Pub Expected Status {i}")
            else:
                print("There is no any online node yet...")

    def _node_status_callback(self, msg):
        self.online_nodes.add(msg.transfer.source_node_id)
        print(f"Receive NodeStatus from node {msg.transfer.source_node_id}.")


class CommandTypes:
    RAW = {"name": "raw", "class": PWMRawCommander}
    ARRAY = {"name": "array", "class": PWMArrayCommander}


class PWMCommanderSelector:
    def __init__(
        self,
        command_type: str,
    ):
        self.commander = None
        if command_type == CommandTypes.RAW["name"]:
            self.commander = CommandTypes.RAW["class"]
        else:
            self.commander = CommandTypes.ARRAY["class"]


def main():
    parser = argparse.ArgumentParser(description=
                "Simulated DroneCAN Commander for RawCommand and ArrayCommand.\
                 Sends specified in command msg and the expected Status of receiver")
    name_key = "name"
    parser.add_argument(
        "--port",
        "-p",
        type=str,
        help="CAN sniffer port. Example: slcan:/dev/ttyACM0",
        nargs="?",
        default="slcan0",
    )
    parser.add_argument(
        "--command",
        "-c",
        type=str,
        help=f"uavcan command type. \
            Example: {CommandTypes.RAW[name_key]} tends to esc.RawCommand, \
                {CommandTypes.ARRAY[name_key]} - actuator.ArrayCommand",
        nargs="?",
        default="raw",
    )
    args = parser.parse_args()
    selector = PWMCommanderSelector(args.command)
    commander = selector.commander(args.port)
    commander.spin()


if __name__ == "__main__":
    main()
