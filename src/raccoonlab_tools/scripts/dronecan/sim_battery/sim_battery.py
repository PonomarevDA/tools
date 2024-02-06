#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
import argparse
import dronecan
from dronecan import uavcan

class Battery:
    def __init__(self, node) -> None:
        self.node = node
        self.battery_msg = uavcan.equipment.power.BatteryInfo(
            temarature = 310,
            voltage = 48.5,
            current = 0.0,
            state_of_health_pct = 127,
            state_of_charge_pct = 100,
            model_name = "simulated_battery"
        )
        self.node.add_handler(uavcan.protocol.NodeStatus, self._node_status_callback)
        self.online_nodes = set()

    def spin(self):
        while True:
            self.node.spin(0.5)
            if len(self.online_nodes) >= 1:
                self.node.broadcast(self.battery_msg)
                print('Pub BatteryInfo')
            else:
                print("There is no any online node yet...")

    def _node_status_callback(self, msg):
        self.online_nodes.add(msg.transfer.source_node_id)
        print(f"Receive NodeStatus from node {msg.transfer.source_node_id}.")

if __name__ =="__main__":
    parser = argparse.ArgumentParser(description='Simulated DroneCAN Battery')
    parser.add_argument("--port",
                        default='slcan:/dev/ttyACM0',
                        type=str,
                        help="CAN device name. Examples: slcan:/dev/ttyACM0, slcan0")
    args = parser.parse_args()

    node = dronecan.make_node(args.port, node_id=100, bitrate=1000000, baudrate=1000000)

    battery = Battery(node)
    battery.spin()
