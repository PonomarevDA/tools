#!/usr/bin/env python3
import asyncio
import sys
import time
import pathlib
import re

# pylint: disable-next=wrong-import-position
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "build/nunavut_out"))
import pycyphal.application
# pylint: disable=import-error
import uavcan.node
import uavcan.node.Heartbeat_1_0
import uavcan.node.GetInfo_1_0
import uavcan.register
import uavcan.register.List_1_0


async def main(dest_node_id):
    software_version = uavcan.node.Version_1_0(major=1, minor=0)
    node_info = uavcan.node.GetInfo_1_0.Response(
        software_version,
        name="co.raccoonlab.spec_checker"
    )
    cyphal_node = pycyphal.application.make_node(node_info)
    cyphal_node.heartbeat_publisher.mode = uavcan.node.Mode_1_0.OPERATIONAL
    cyphal_node.start()

    await NodeNameChecker(cyphal_node, dest_node_id).run()
    await HearbeatFrequencyChecker(cyphal_node, dest_node_id).run()
    await RegistersNameChecker(cyphal_node, dest_node_id).run()
    await PortRegistersTypeChecker(cyphal_node, dest_node_id).run()
    await DefaultRegistersExistanceChecker(cyphal_node, dest_node_id).run()


def np_array_to_string(np_array):
    return "".join([chr(item) for item in np_array])


class NodeNameChecker:
    def __init__(self, cyphal_node, dest_node_id):
        self._node = cyphal_node
        self._dest_node_id = dest_node_id

    async def run(self, number_of_attempts=2):
        request = uavcan.node.GetInfo_1_0.Request()
        client = self._node.make_client(uavcan.node.GetInfo_1_0, self._dest_node_id)
        for _ in range(number_of_attempts):
            response = await client.call(request)
            if response is not None:
                name = np_array_to_string(response[0].name)
                print(self.check_node_name(name), name)
                break
            await asyncio.sleep(1)

    @staticmethod
    def check_node_name(node_name):
        pattern = r'^[a-z0-9]+(\.[a-z0-9]+){3}$'
        return re.match(pattern, node_name) is not None


class HearbeatFrequencyChecker:
    def __init__(self, cyphal_node, dest_node_id):
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

async def request_regiter_names(cyphal_node, dest_node_id, max_register_amount=256):
    register_names = []
    list_request = uavcan.register.List_1_0.Request()
    list_client = cyphal_node.make_client(uavcan.register.List_1_0, dest_node_id)
    for _ in range(max_register_amount):
        list_response = await list_client.call(list_request)
        if list_response is None:
            return None

        register_name = np_array_to_string(list_response[0].name.name)
        if len(register_name) == 0:
            break

        register_names.append(register_name)
        await asyncio.sleep(0.001)
        list_request.index += 1

    return register_names

class RegistersNameChecker:
    def __init__(self, cyphal_node, dest_node_id):
        self._node = cyphal_node
        self._dest_node_id = dest_node_id

    async def run(self):
        register_names = await request_regiter_names(self._node, self._dest_node_id)

        for register_name in register_names:
            if not self.check_register_name(register_name):
                print(f"{register_name} has wrong name pattern")

    @staticmethod
    def check_register_name(register_name):
        pattern = r'^[a-z][a-z0-9._]*(\.[a-z0-9._]+)+$'
        return re.match(pattern, register_name) is not None

class PortRegistersTypeChecker:
    def __init__(self, cyphal_node, dest_node_id):
        self._node = cyphal_node
        self._dest_node_id = dest_node_id

    async def run(self):
        is_test_successfull = True
        register_names = await request_regiter_names(self._node, self._dest_node_id)

        access_request = uavcan.register.Access_1_0.Request()
        access_client = self._node.make_client(uavcan.register.Access_1_0, self._dest_node_id)
        for register_name in register_names:
            if not register_name.startswith("uavcan.") or not register_name.endswith(".id"):
                continue

            access_request.name.name = register_name
            access_response = await access_client.call(access_request)
            if access_response is None:
                is_test_successfull = False
                continue

            if access_response[0].value.natural16 is None:
                is_test_successfull = False
                print(f"{register_name} should have natural16 type")

        return is_test_successfull

class DefaultRegistersExistanceChecker:
    def __init__(self, cyphal_node, dest_node_id):
        self._node = cyphal_node
        self._dest_node_id = dest_node_id

    async def run(self):
        is_test_successfull = True

        register_names = [
            "uavcan.node.id",
            "uavcan.node.name",
        ]
        access_request = uavcan.register.Access_1_0.Request()
        access_client = self._node.make_client(uavcan.register.Access_1_0, self._dest_node_id)
        access_response = None
        for register_name in register_names:
            access_request.name.name = register_name
            access_response = await access_client.call(access_request)
            if access_response is None:
                is_test_successfull = False
                continue

            if access_response[0].value.empty is not None:
                print(f"{register_name} is not exist")

        return is_test_successfull

if __name__ == "__main__":
    asyncio.run(main(dest_node_id=50))
