#!/usr/bin/env python3
import asyncio
import sys
import time
import pathlib
import re

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "build/nunavut_out"))
import pycyphal.application
import uavcan.node
import uavcan.node.Heartbeat_1_0
import uavcan.node.GetInfo_1_0


async def check_cyphal_specification():
    software_version = uavcan.node.Version_1_0(major=1, minor=0)
    node_info = uavcan.node.GetInfo_1_0.Response(software_version, name="spec_checker")
    cyphal_node = pycyphal.application.make_node(node_info)
    cyphal_node.heartbeat_publisher.mode = uavcan.node.Mode_1_0.OPERATIONAL
    cyphal_node.start()

    await NodeNameChecker(cyphal_node).run()
    await HearbeatFrequencyChecker(cyphal_node).run()


class NodeNameChecker:
    def __init__(self, cyphal_node, dest_node_id=50):
        self._node = cyphal_node
        self._dest_node_id = dest_node_id

    async def run(self, number_of_attempts=2):
        request = uavcan.node.GetInfo_1_0.Request()
        client = self._node.make_client(uavcan.node.GetInfo_1_0, self._dest_node_id)
        for _ in range(number_of_attempts):
            response = await client.call(request)
            if response is not None:
                name = "".join([chr(item) for item in response[0].name])
                print(self.check_node_name(name), name)
                break
            await asyncio.sleep(1)

    @staticmethod
    def check_node_name(node_name):
        pattern = r'^[a-z0-9]+(\.[a-z0-9]+){3}$'
        return re.match(pattern, node_name) is not None


class HearbeatFrequencyChecker:
    def __init__(self, cyphal_node, dest_node_id=50):
        self._node = cyphal_node
        self._dest_node_id = dest_node_id
        self._heartbeat_timestamps = []

    async def run(self):
        sub = self._node.make_subscriber(uavcan.node.Heartbeat_1_0)
        sub.receive_in_background(self._heartbeat_callback)
        await asyncio.sleep(9)
        sub.close()
        periods = self.calculate_time_differences(self._heartbeat_timestamps)
        if periods is None or periods[0] < 1 or periods[1] > 3:
            print(f"Heartbeat is bad: {periods}")
        else:
            print(f"Heartbeat is fine: {periods}")

    async def _heartbeat_callback(self, _, transfer_from):
        if transfer_from.source_node_id == self._dest_node_id:
            self._heartbeat_timestamps.append(time.time())

    @staticmethod
    def calculate_time_differences(timestamps):
        if len(timestamps) < 3:
            return None
        
        periods = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]
        return min(periods), max(periods)


if __name__ == "__main__":
    asyncio.run(check_cyphal_specification())
