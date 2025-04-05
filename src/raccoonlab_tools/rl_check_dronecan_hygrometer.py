#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2025 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
"""
Subscribe on Humidity topic
"""
import os
import sys
import time
import errno
import logging
import argparse
from typing import Optional
import platform
import dronecan
import netifaces

logger = logging.getLogger("hygrometer")

def create_dronecan_node(port: Optional[str],
                         node_id: int = 42,
                         bitrate=1_000_000,
                         baudrate=1_000_000) -> dronecan.node.Node:
    if port is None:
        if platform.system() != "Linux":
            logger.error("Port is not specified. Auto detection supported only on Linux.")
            raise OSError(errno.ENODEV, "No such device")

        if "slcan0" in netifaces.interfaces():
            port = "slcan0"
        elif os.path.exists("/dev/ttyACM0"):
            port = 'slcan:/dev/ttyACM0'
        else:
            logger.error(("Neither slcan0 nor /dev/ttyACM0 exists. "
                          "Please, check CAN-sniffer connection or specify the port manually."))
            raise OSError(errno.ENODEV, "No such device")

    node_info = dronecan.uavcan.protocol.GetNodeInfo.Response()
    node_info.name = 'co.rl.check_hygrometer'

    node = dronecan.make_node(port,
                              node_id=node_id,
                              bitrate=bitrate,
                              baudrate=baudrate,
                              node_info=node_info)

    node.mode = dronecan.uavcan.protocol.NodeStatus().MODE_OPERATIONAL

    logger.info("DroneCAN node successfully created on port %s.", port)
    return node


class Hygrometer:
    def __init__(self, node: Optional[dronecan.node.Node]):
        self.node = create_dronecan_node(port, node_id) if node is None else node

        self.node.add_handler(dronecan.dronecan.sensors.hygrometer.Hygrometer, self._callback)

        self.msg = {
            "humidity": None,
            "temperature": None,
            "timestamp": 0,
        }

    def get(self) -> dict:
        return self.msg

    def __str__(self) -> str:
        if time.time() > self.msg["timestamp"] + 5.0:
            return "No data"

        humidity = self.msg["humidity"]
        temperature = self.msg["temperature"]
        return f"Humidity {humidity}%, temperature {temperature}°C"

    def spin(self, timeout: float) -> None:
        try:
            self.node.spin(timeout)
        except dronecan.driver.common.DriverError:
            pass

    def _callback(self, event: dronecan.node.TransferEvent) -> None:
        is_first_callback = self.msg["timestamp"] == 0

        self.msg["humidity"] = round(event.message.humidity)
        self.msg["temperature"] = round(event.message.temperature)
        self.msg["timestamp"] = time.time()

        if is_first_callback:
            logger.info("Handling first callback %s", self.get())


if __name__ =="__main__":
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.ERROR
    )
    logger.setLevel(logging.DEBUG)

    logging.getLogger("dronecan").setLevel(logging.WARNING)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default=None, type=str, help="CAN: slcan:/dev/ttyACM0 slcan0")
    parser.add_argument("--node-id", default=60, type=str, help="Node ID from 1 to 127")
    args = parser.parse_args()

    try:
        node = create_dronecan_node(args.port, args.node_id)
    except OSError:
        sys.exit(1)

    try:
        hygrometer = Hygrometer(node)

        while True:
            hygrometer.spin(0.1)
            logger.info("Hygrometer: %s", str(hygrometer))

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")
