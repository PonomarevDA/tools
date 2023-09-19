#!/usr/bin/env python3
import dronecan
from dronecan import uavcan


class DronecanGpsMagBaroChecker:
    def __init__(self, dronecan_node):
        self._dronecan_node = dronecan_node
        self._dronecan_node.add_handler(uavcan.equipment.gnss.Fix2, self._callback)
        self._sats_used = None
        self._required_sats = 8

    def is_valid(self):
        return self._sats_used is not None and self._sats_used >= self._required_sats

    def get_sats_used(self):
        return self._sats_used

    def __str__(self) -> str:
        if self._sats_used is None:
            description = "Fix2 has not been published published yet."
        elif self._sats_used == 0:
            description = "Not satelites. Put the device outside with clear view of the sky."
        elif self._sats_used < self._required_sats:
            description = f"Satelites: {self._sats_used}. We need more."
        else:
            description = f"Setelites: {self._sats_used}. Goood!"
        return description

    def _callback(self, msg):
        payload = msg.transfer.payload
        self._sats_used = payload.sats_used


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description='GNSS node checker')
    parser.add_argument("--port", default='slcan0', type=str, help="CAN sniffer port. Example: slcan0")
    parser.add_argument("--timeout", default=10, type=int, help="Waiting for satelites duration. Default 90 seconds")
    args = parser.parse_args()

    dronecan_node = dronecan.make_node(args.port, node_id=100, bitrate=1000000)

    checker = DronecanGpsMagBaroChecker(dronecan_node)
    dronecan_node.spin(0.5)
    for elapsed_time in range(0, args.timeout, 5):
        print(f"{elapsed_time}/{args.timeout}: {checker}")
        if checker.is_valid():
            break
        dronecan_node.spin(5)
