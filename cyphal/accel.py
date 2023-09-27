#!/usr/bin/env python3
import asyncio
import sys
import pathlib
import time

# pylint: disable-next=wrong-import-position
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "build/nunavut_out"))
import pycyphal.application
# pylint: disable=import-error
import uavcan.node
import uavcan.si.unit.acceleration.Vector3_1_0

class AccelerometerChecker:
    def __init__(self, cyphal_node, port_id):
        self._node = cyphal_node
        self._port_id = port_id
        self.max_delay_ms = 0
        self.min_delay_ms = 1000
        self.prev_print_ts = time.time()
        self.prev_ts = time.time()
        self.msg_counter = 0

    async def run(self):
        sub = self._node.make_subscriber(uavcan.si.unit.acceleration.Vector3_1_0, self._port_id)
        sub.receive_in_background(self._callback)
        await asyncio.sleep(60*60*24)

    async def _callback(self, msg, transfer_from):
        crnt_ts = time.time()

        delay_ms = round((crnt_ts - self.prev_ts) * 1000, 2)
        if delay_ms > self.max_delay_ms:
            self.max_delay_ms = delay_ms
        if delay_ms < self.min_delay_ms:
            self.min_delay_ms = delay_ms

        self.prev_ts = crnt_ts
        self.msg_counter += 1

        if crnt_ts > self.prev_print_ts + 1.0:
            print(self.msg_counter, self.max_delay_ms, self.min_delay_ms)
            self.max_delay_ms = 0
            self.min_delay_ms = 1000
            self.prev_print_ts = crnt_ts
            self.msg_counter = 0


async def main(port_id):
    software_version = uavcan.node.Version_1_0(major=1, minor=0)
    node_info = uavcan.node.GetInfo_1_0.Response(
        software_version,
        name="co.raccoonlab.imu_checker"
    )
    cyphal_node = pycyphal.application.make_node(node_info)
    cyphal_node.heartbeat_publisher.mode = uavcan.node.Mode_1_0.OPERATIONAL
    cyphal_node.start()

    await AccelerometerChecker(cyphal_node, port_id).run()


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Cyphal specification checker')
    parser.add_argument("--accel", default='2400', type=int, help="Acceleromenter port ID")
    args = parser.parse_args()
    asyncio.run(main(dest_node_id=args.accel))
