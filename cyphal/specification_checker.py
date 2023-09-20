#!/usr/bin/env python3
import asyncio
import sys
import time
import pathlib
import random
import string
import re

# pylint: disable-next=wrong-import-position
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "build/nunavut_out"))
import pycyphal.application
# pylint: disable=import-error
import uavcan.node
import uavcan.node.Heartbeat_1_0
import uavcan.node.GetInfo_1_0
import uavcan.node.port.List_1_0
import uavcan.register
import uavcan.register.List_1_0


def np_array_to_string(np_array):
    return "".join([chr(item) for item in np_array])

async def retrive_all_regiter_names(cyphal_node, dest_node_id, max_register_amount=256):
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


class BaseChecker:
    def __init__(self) -> None:
        pass

    async def test(self):
        details = await self._run()
        if len(details) != 0:
            print(f"Violation of {self.__doc__}")
            print(details)


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
                break
            await asyncio.sleep(1)

        if response is None:
            print("The node has not respond on GetInfo request.")
            return

        name = np_array_to_string(response[0].name)
        if not self.check_node_name(name):
            print(f"The node name {name} does not follow the node name pattern.")

    @staticmethod
    def check_node_name(node_name):
        pattern = r'^[a-z0-9_\-]+(\.[a-z0-9_\-]+)+$'
        return re.match(pattern, node_name) is not None


class HearbeatFrequencyChecker:
    """https://github.com/OpenCyphal/public_regulated_data_types/blob/master/uavcan/node/7509.Heartbeat.1.0.dsdl"""
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
        if periods is None or periods[0] < 0.9 or periods[1] > 3:
            eror_msg = f"Violation of: {self.__doc__} \n" + \
                    f"Details: got {len(self._heartbeat_timestamps)} heartbeats within 9 sec" + \
                    f" (min period = {periods[0]}, max period = {periods[1]})."
            print(eror_msg)

    async def _heartbeat_callback(self, _, transfer_from):
        if transfer_from.source_node_id == self._dest_node_id:
            self._heartbeat_timestamps.append(time.time())

    @staticmethod
    def calculate_time_differences(timestamps):
        if len(timestamps) < 3:
            return None

        periods = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]
        return min(periods), max(periods)


class RegistersNameChecker(BaseChecker):
    """https://github.com/OpenCyphal/public_regulated_data_types/blob/master/uavcan/register/384.Access.1.0.dsdl"""
    def __init__(self, cyphal_node, dest_node_id):
        self._node = cyphal_node
        self._dest_node_id = dest_node_id

    async def _run(self) -> str:
        details = ""
        register_names = await retrive_all_regiter_names(self._node, self._dest_node_id)

        for register_name in register_names:
            if not self.check_register_name(register_name):
                if len(details) != 0:
                    details += "\n"
                details += f"- `{register_name}` register has wrong name pattern"

        return details

    @staticmethod
    def check_register_name(register_name):
        pattern = r'^[a-z][a-z0-9._]*(\.[a-z0-9._]+)+$'
        return re.match(pattern, register_name) is not None


class PortRegistersTypeChecker(BaseChecker):
    """https://github.com/OpenCyphal/public_regulated_data_types/blob/master/uavcan/register/384.Access.1.0.dsdl"""
    def __init__(self, cyphal_node, dest_node_id):
        self._node = cyphal_node
        self._dest_node_id = dest_node_id

    async def _run(self):
        details = ""
        all_register_names = await retrive_all_regiter_names(self._node, self._dest_node_id)

        access_request = uavcan.register.Access_1_0.Request()
        access_client = self._node.make_client(uavcan.register.Access_1_0, self._dest_node_id)
        for register_name in all_register_names:
            port_type, port_reg_type = self.get_port_type_by_register_name(register_name)
            if port_type is None or port_reg_type is None:
                continue

            access_request.name.name = register_name
            access_response = await access_client.call(access_request)

            if access_response is None:
                details += f"- {register_name} retrive failed\n"
                continue

            access_response = access_response[0]
            if port_reg_type == "id":
                if access_response.value.natural16 is None:
                    details += f"- {register_name} should have natural16 type, but it is not.\n"
                elif access_response._mutable is False or access_response.persistent is False:
                    details += f"- {register_name} should be mutable and persistent, but it is {access_response}.\n"
            elif port_reg_type == "type":
                if access_response.value.string is None:
                    details += f"- {register_name} should have string type, but it is not.\n"
                elif access_response._mutable is True or access_response.persistent is False:
                    details += f"- {register_name} should be mutable and persistent, but it is {access_response}.\n"

        return details

    @staticmethod
    def get_port_type_by_register_name(reg):
        port_type = None
        port_reg_type = None

        if reg.startswith("uavcan.pub"):
            port_type = 'pub'
        elif reg.startswith("uavcan.sub"):
            port_type = 'sub'
        elif reg.startswith("uavcan.cln"):
            port_type = 'cln'
        elif reg.startswith("uavcan.srv"):
            port_type = 'srv'

        if reg.endswith(".id"):
            port_reg_type = "id"
        elif reg.endswith(".type"):
            port_reg_type = "type"

        return port_type, port_reg_type

class PersistentMemoryChecker(BaseChecker):
    """Persistent memory check: 1. set random, 2. save, 3. reboot, 4. get"""
    def __init__(self, cyphal_node, dest_node_id):
        self._node = cyphal_node
        self._dest_node_id = dest_node_id
        self._register_name = "uavcan.node.description"
        self._test_value = ''.join(random.choices(string.ascii_lowercase, k=10))

        self._access_client = self._node.make_client(uavcan.register.Access_1_0, self._dest_node_id)
        self._cmd_client = self._node.make_client(uavcan.node.ExecuteCommand_1_1, self._dest_node_id)

    async def _run(self):
        details = ""

        set_request = uavcan.register.Access_1_0.Request()
        set_request.name.name = self._register_name
        set_request.value.string = uavcan.primitive.String_1_0(self._test_value)
        access_response = await self._access_client.call(set_request)
        if access_response is None:
            return "1/4. Access retrive failed"
        value = np_array_to_string(access_response[0].value.string.value)
        if value != self._test_value:
            return f"1/4. Accees expected {self._test_value}, got {value}"

        save_request = uavcan.node.ExecuteCommand_1_1.Request(command = 65530)
        cmd_response = await self._cmd_client.call(save_request)
        if cmd_response is None:
            return f"2/4. ExecuteCommand retrive failed"

        reboot_request = uavcan.node.ExecuteCommand_1_1.Request(command = 65535)
        await self._cmd_client.call(reboot_request)

        get_request = uavcan.register.Access_1_0.Request()
        get_request.name.name = self._register_name
        access_response = await self._access_client.call(set_request)
        if access_response is None:
            return "4/4. Access retrive failed"
        value = np_array_to_string(access_response[0].value.string.value)
        if value != self._test_value:
            return f"4/4. Accees expected {self._test_value}, got {value}"

        return details

class DefaultRegistersExistanceChecker:
    """https://github.com/OpenCyphal/public_regulated_data_types/blob/master/uavcan/register/384.Access.1.0.dsdl"""
    def __init__(self, cyphal_node, dest_node_id):
        self._node = cyphal_node
        self._dest_node_id = dest_node_id

    async def run(self):
        is_test_successfull = True

        register_names = [
            "uavcan.node.id",
            "uavcan.node.description",
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

class PortListServersChecker:
    """https://github.com/OpenCyphal/public_regulated_data_types/blob/master/uavcan/node/port/7510.List.1.0.dsdl"""
    def __init__(self, cyphal_node, dest_node_id):
        self._node = cyphal_node
        self._dest_node_id = dest_node_id
        self._port_list_msg = None

    async def run(self):
        sub = self._node.make_subscriber(uavcan.node.port.List_1_0)
        sub.receive_in_background(self._port_list_callback)

        for _ in range(11):
            await asyncio.sleep(1)
            if self._port_list_msg is not None:
                break

        if self._port_list_msg is None:
            print("uavcan.port.List was not published")
        elif not self.is_enough_servers(self._port_list_msg.servers.mask):
            print(f"Violation of: {self.__doc__}")
            print("Details: uavcan.port.List doesn't support required services:")
            print(f"- 384 (register.Access): {self._port_list_msg.servers.mask[384]}")
            print(f"- 385 (register.List): {self._port_list_msg.servers.mask[385]}")
            print(f"- 430 (GetInfo): {self._port_list_msg.servers.mask[430]}")
            print(f"- 435 (ExecuteCommand): {self._port_list_msg.servers.mask[435]}")

    async def _port_list_callback(self, msg, _):
        self._port_list_msg = msg

    @staticmethod
    def is_enough_servers(mask):
        if mask[384] == True and mask[385] == True and mask[430] == True and mask[435] == True:
            return True

        return False


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
    await RegistersNameChecker(cyphal_node, dest_node_id).test()
    await PortRegistersTypeChecker(cyphal_node, dest_node_id).test()
    await DefaultRegistersExistanceChecker(cyphal_node, dest_node_id).run()
    await PortListServersChecker(cyphal_node, dest_node_id).run()
    await PersistentMemoryChecker(cyphal_node, dest_node_id).test()

def test_cyphal_standard(dest_node_id):
    asyncio.run(main(dest_node_id))


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Cyphal specification checker')
    parser.add_argument("--node", default='50', type=int, help="Destination node identifier")
    args = parser.parse_args()
    test_cyphal_standard(dest_node_id=args.node)
