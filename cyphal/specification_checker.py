#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
import asyncio
import time
import random
import string
import re
import pytest

import pycyphal.application
# pylint: disable=import-error
import uavcan
import uavcan.node.port.List_1_0
from utils import NodeFinder, RegisterInterface, PortRegisterInterface

# We are going to ignore a few checks for the given nodes:
DEBUGGING_TOOLS_NAME = [
    'org.opencyphal.yakut.monitor',
]

@pytest.fixture(autouse=True)
async def run_around_tests():
    """
    We need to keep a pause before exit.
    Task was destroyed but it is pending
    """
    yield
    await asyncio.sleep(0.001)

@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class GlobalCyphalNode:
    cyphal_node = None

    @staticmethod
    def get_node() -> pycyphal.application._node.Node:
        if GlobalCyphalNode.cyphal_node is not None:
            return GlobalCyphalNode.cyphal_node

        GlobalCyphalNode.cyphal_node = pycyphal.application.make_node(
            uavcan.node.GetInfo_1_0.Response(
                uavcan.node.Version_1_0(major=1, minor=0),
                name="co.raccoonlab.spec_checker"
        ))

        GlobalCyphalNode.cyphal_node.heartbeat_publisher.mode = uavcan.node.Mode_1_0.OPERATIONAL
        GlobalCyphalNode.cyphal_node.start()
        return GlobalCyphalNode.cyphal_node

@pytest.mark.asyncio
class TestNodeHeartbeat:
    """5.3.2 Node heartbeat (uavcan.node.Heartbeat)"""
    timestamps = []
    uptimes = []
    data_collected = False

    @staticmethod
    async def test_frequency():
        """A node must publish Heartbeat with constant frequency 1 Hz"""
        await TestNodeHeartbeat._collect_heartbeats()

        for idx in range(len(TestNodeHeartbeat.timestamps) - 1):
            period = TestNodeHeartbeat.timestamps[idx+1] - TestNodeHeartbeat.timestamps[idx]
            assert pytest.approx(1.0, abs=0.05) == period

    @staticmethod
    async def test_uptime():
        """The node is not expected to be restarted during the test, check uptime"""
        await TestNodeHeartbeat._collect_heartbeats()

        assert (TestNodeHeartbeat.uptimes[-1] - TestNodeHeartbeat.uptimes[0]) == 4

    @staticmethod
    async def _collect_heartbeats():
        """ Let's collect Heartbeat of the target node for 5.5 seconds and check last 5 of them"""
        if TestNodeHeartbeat.data_collected:
            return

        cyphal_node = GlobalCyphalNode.get_node()
        dest_node_id = await NodeFinder(cyphal_node).find_online_node()
        sub = cyphal_node.make_subscriber(uavcan.node.Heartbeat_1_0)
        TestNodeHeartbeat.timestamps = []
        TestNodeHeartbeat.uptimes = []

        time_left = 5.5
        end_time = time.time() + time_left
        while time_left > 0:
            transfer_from = await sub.receive_for(time_left)
            if transfer_from is not None and transfer_from[1].source_node_id == dest_node_id:
                TestNodeHeartbeat.timestamps.append(time.time())
                TestNodeHeartbeat.uptimes.append(transfer_from[0].uptime)
            time_left = end_time - time.time()
        sub.close()

        assert len(TestNodeHeartbeat.timestamps) >= 5
        assert len(TestNodeHeartbeat.uptimes) >= 5
        TestNodeHeartbeat.timestamps = TestNodeHeartbeat.timestamps[-5:]
        TestNodeHeartbeat.uptimes = TestNodeHeartbeat.uptimes[-5:]
        TestNodeHeartbeat.data_collected = True


@pytest.mark.asyncio
class TestGenericNodeInformation:
    """5.3.3. Generic node information (uavcan.node.GetInfo)"""
    data_collected = False
    get_info_response = uavcan.node.GetInfo_1_0.Response()

    @staticmethod
    async def test_protocol_version():
        """The Protocol version field should be filled in."""
        get_info = await TestGenericNodeInformation._get_info()
        protocol_version = get_info.protocol_version
        assert not (protocol_version.major == 0 and protocol_version.minor == 0)

    @staticmethod
    async def test_hardware_version():
        """Hardware version field should be filled."""
        get_info = await TestGenericNodeInformation._get_info()
        name = "".join([chr(item) for item in get_info.name])
        if name not in DEBUGGING_TOOLS_NAME:
            hardware_version = get_info.hardware_version
            assert not (hardware_version.major == 0 and hardware_version.minor == 0)

    @staticmethod
    async def test_software_version():
        """Softwarte version field should be filled."""
        get_info = await TestGenericNodeInformation._get_info()
        software_version = get_info.software_version
        assert not (software_version.major == 0 and software_version.minor == 0)

    @staticmethod
    async def test_software_vcs_revision_id():
        """Software VSC field should be filled."""
        get_info = await TestGenericNodeInformation._get_info()
        name = "".join([chr(item) for item in get_info.name])
        if name not in DEBUGGING_TOOLS_NAME:
            assert get_info.software_vcs_revision_id != 0

    @staticmethod
    async def test_unique_id():
        """Software UID field should be filled."""
        get_info = await TestGenericNodeInformation._get_info()
        unique_id_is_valid = any(byte != 0 for byte in get_info.unique_id)
        assert unique_id_is_valid

    @staticmethod
    @pytest.mark.skip(reason="not yet")
    async def test_software_image_crc():
        """Software Image CRC field should be filled."""
        get_info = await TestGenericNodeInformation._get_info()
        software_image_crc_is_valid = any(byte != 0 for byte in get_info.software_image_crc)
        assert software_image_crc_is_valid

    @staticmethod
    @pytest.mark.skip(reason="not yet")
    async def test_certificate_of_authenticity():
        """he certificate of authenticity (COA) field should be filled."""
        get_info = await TestGenericNodeInformation._get_info()
        coa = get_info.certificate_of_authenticity
        coa_is_valid = any(byte != 0 for byte in coa)
        assert coa_is_valid

    @staticmethod
    async def test_node_name():
        """
        Node name pattern: com.manufacturer.project.product
        Examples of correct names:
        - org.opencyphal.yakut.monitor
        - co.raccoonlab.gps_mag_baro
        """
        get_info_response = await TestGenericNodeInformation._get_info()
        name = "".join([chr(item) for item in get_info_response.name])
        assert TestGenericNodeInformation._check_node_name(name), name

    @staticmethod
    def _check_node_name(node_name : str) -> bool:
        pattern = r'^[a-z0-9_\-]+(\.[a-z0-9_\-]+)+$'
        return re.match(pattern, node_name) is not None

    @staticmethod
    async def _get_info() -> uavcan.node.GetInfo_1_0.Response:
        if TestGenericNodeInformation.data_collected:
            return TestGenericNodeInformation.get_info_response

        cyphal_node = GlobalCyphalNode.get_node()
        dest_node_id = await NodeFinder(cyphal_node).find_online_node()

        client = cyphal_node.make_client(uavcan.node.GetInfo_1_0, dest_node_id)
        get_info_response = await client.call(uavcan.node.GetInfo_1_0.Request())
        client.close()
        assert get_info_response is not None
        get_info_response = get_info_response[0]
        TestGenericNodeInformation.get_info_response = get_info_response
        TestGenericNodeInformation.data_collected = True
        return TestGenericNodeInformation.get_info_response


@pytest.mark.asyncio
class TestBusDataFlowMonitoring:
    """5.3.4. Bus data flow monitoring (uavcan.node.port)"""
    data_collected = False
    dest_node_name = ""
    port_list = uavcan.node.port.List_1_0()

    @staticmethod
    async def test_reigister_interface_is_supported():
        port_list = await TestBusDataFlowMonitoring._collect_port_list()
        assert port_list.servers.mask[384], "register.Access is not supported"
        assert port_list.servers.mask[385], "register.List is not supported"

    @staticmethod
    async def test_get_info_is_supported():
        port_list = await TestBusDataFlowMonitoring._collect_port_list()
        assert port_list.servers.mask[430], "GetInfo is not supported"

    @staticmethod
    async def test_execute_command_is_supported():
        port_list = await TestBusDataFlowMonitoring._collect_port_list()
        dest_node_name = TestBusDataFlowMonitoring.dest_node_name
        if dest_node_name not in DEBUGGING_TOOLS_NAME:
            assert port_list.servers.mask[435], "ExecuteCommand is not supported"

    @staticmethod
    async def _collect_port_list() -> uavcan.node.port.List_1_0:
        if TestBusDataFlowMonitoring.data_collected:
            return TestBusDataFlowMonitoring.port_list

        cyphal_node = GlobalCyphalNode.get_node()
        node_finder = NodeFinder(cyphal_node)

        tested_node_info = await node_finder.get_tested_node_info()
        TestBusDataFlowMonitoring.dest_node_name = tested_node_info['name']

        port_list = await node_finder.get_port_list()
        assert port_list is not None, "uavcan.port.List was not published!"
        TestBusDataFlowMonitoring.port_list = port_list

        TestBusDataFlowMonitoring.data_collected = True
        return TestBusDataFlowMonitoring.port_list

@pytest.mark.asyncio
class TestGenericNodeCommands():
    """
    5.3.8. Generic node commands (uavcan.node.ExecuteCommand)
    """


@pytest.mark.asyncio
class TestRegisterInterface:
    """5.3.10. Register interface"""
    register_list = []

    @staticmethod
    async def test_registers_name():
        """
        Register name should contain only:
        - Lowercase ASCII alphanumeric characters (a-z, 0-9)
        - Full stop (.)
        - Low line (underscore) (_)
        With the following limitations/recommendations:
        - The name shall not begin with a decimal digit (0-9).
        - The name shall neither begin nor end with a full stop.
        - A low line shall not be followed by a non-alphanumeric character.
        - The name should contain at least one full stop character.
        """

        register_names = await TestRegisterInterface._collect_register_list()
        for register_name in register_names:
            assert TestRegisterInterface._check_register_name(register_name)

    @staticmethod
    async def test_default_registers_existance():
        """A few registers must be implemented in any node"""
        REQUIRED_REGISTERS = [
            "uavcan.node.id",
            "uavcan.node.description",
        ]

        register_list = await TestRegisterInterface._collect_register_list()
        assert all(required_register in register_list for required_register in REQUIRED_REGISTERS)


    @staticmethod
    async def test_port_register_types():
        cyphal_node = GlobalCyphalNode.get_node()
        dest_node_id = await NodeFinder(cyphal_node).find_online_node()
        register_interface = RegisterInterface(cyphal_node)
        register_list = await register_interface.register_list(dest_node_id)

        access_request = uavcan.register.Access_1_0.Request()
        access_client = cyphal_node.make_client(uavcan.register.Access_1_0, dest_node_id)

        print("Check port registers type:")
        for register_name in register_list:
            port_type, port_reg_type = PortRegisterInterface.get_port_type(register_name)
            if port_type is None or port_reg_type is None:
                print(f"- {register_name :<30} skip")
                continue

            access_request.name.name = register_name
            access_response = await access_client.call(access_request)

            assert access_response is not None

            access_response = access_response[0]
            if port_reg_type == "id":
                assert access_response.value.natural16 is not None, f"- {register_name} should have natural16 type, but it is not"
                assert access_response._mutable and access_response.persistent, f"- {register_name} should be mutable and persistent, but it is {access_response}"
                print(f"- {register_name :<30} is natural16, mutable and persistent.")
            elif port_reg_type == "type":
                assert access_response.value.string is not None, f"- {register_name} should have string type, but it is not"
                assert access_response._mutable is False and access_response.persistent is True, f"- {register_name} should be immutable and persistent, but it is {access_response}"
                print(f"- {register_name :<30} is string, immutable and persistent")

    @staticmethod
    def _check_register_name(register_name):
        pattern = r'^[a-z][a-z0-9._]*(\.[a-z0-9._]+)+$'
        return re.match(pattern, register_name) is not None

    @staticmethod
    async def _collect_register_list() -> list:
        if len(TestRegisterInterface.register_list) != 0:
            return TestRegisterInterface.register_list

        cyphal_node = GlobalCyphalNode.get_node()
        dest_node_id = await NodeFinder(cyphal_node).find_online_node()
        register_names = await RegisterInterface(cyphal_node).register_list(dest_node_id)
        assert len(register_names) >= 2, "Node should have at least 2 registers!"
        TestRegisterInterface.register_list = register_names
        return TestRegisterInterface.register_list


@pytest.mark.asyncio
class TestPersistentMemory():
    """Persistent memory check: 1. set random, 2. save, 3. reboot, 4. get"""

    @staticmethod
    async def test_persistent_memory() -> None:
        print("TestPersistentMemory:")

        cyphal_node = GlobalCyphalNode.get_node()
        node_finder = NodeFinder(cyphal_node)

        tested_node_info = await node_finder.get_tested_node_info()
        dest_node_name = tested_node_info['name']
        if dest_node_name in DEBUGGING_TOOLS_NAME:
            print("Skip test because yakut doesn't support ExecuteCommand.")
            return

        dest_node_id = await node_finder.find_online_node()
        register_name = "uavcan.node.description"
        random_test_value = ''.join(random.choices(string.ascii_lowercase, k=10))
        cmd_client = cyphal_node.make_client(uavcan.node.ExecuteCommand_1_1, dest_node_id)
        cmd_client.close()

        set_request = uavcan.register.Access_1_0.Request()
        set_request.name.name = register_name
        set_request.value.string = uavcan.primitive.String_1_0(random_test_value)
        access_client = cyphal_node.make_client(uavcan.register.Access_1_0, dest_node_id)
        access_response = await access_client.call(set_request)
        access_client.close()
        assert access_response is not None, "Access retrive failed!"
        value = "".join([chr(item) for item in access_response[0].value.string.value])
        assert value == random_test_value, f"1/4. Accees expected {random_test_value}, got {value}!"
        print(f"- 1/4. y r {dest_node_id} uavcan.node.description {random_test_value} # success")

        save_request = uavcan.node.ExecuteCommand_1_1.Request(command = 65530)
        cmd_client = cyphal_node.make_client(uavcan.node.ExecuteCommand_1_1, dest_node_id)
        cmd_response = await cmd_client.call(save_request)
        cmd_client.close()
        assert cmd_response is not None, "2/4. ExecuteCommand retrive failed!"
        print(f"- 2/4. y r {dest_node_id} 65530 # success")

        reboot_request = uavcan.node.ExecuteCommand_1_1.Request(command = 65535)
        cmd_client = cyphal_node.make_client(uavcan.node.ExecuteCommand_1_1, dest_node_id)
        await cmd_client.call(reboot_request)
        cmd_client.close()
        assert cmd_response is not None, "2/4. ExecuteCommand retrive failed!"
        print(f"- 3/4. y r {dest_node_id} 65535 # success")

        get_request = uavcan.register.Access_1_0.Request()
        get_request.name.name = register_name
        access_client = cyphal_node.make_client(uavcan.register.Access_1_0, dest_node_id)
        access_response = await access_client.call(set_request)
        access_client.close()
        assert access_response is not None, "4/4. Access retrive failed!"
        value = "".join([chr(item) for item in access_response[0].value.string.value])
        assert value == random_test_value, f"4/4. Accees expects {random_test_value}, got {value}!"
        print(f"- 4/4. y r {dest_node_id} uavcan.node.description # success: {random_test_value}")


async def main():
    print("Cyphal specification checker:")
    await TestNodeHeartbeat.test_frequency()
    await TestNodeHeartbeat.test_uptime()

    await TestGenericNodeInformation.test_protocol_version()
    await TestGenericNodeInformation.test_hardware_version()
    await TestGenericNodeInformation.test_software_version()
    await TestGenericNodeInformation.test_software_vcs_revision_id()
    await TestGenericNodeInformation.test_unique_id()
    await TestGenericNodeInformation.test_node_name()

    await TestBusDataFlowMonitoring.test_reigister_interface_is_supported()
    await TestBusDataFlowMonitoring.test_get_info_is_supported()
    await TestBusDataFlowMonitoring.test_execute_command_is_supported()

    await TestRegisterInterface.test_registers_name()
    await TestRegisterInterface.test_default_registers_existance()
    await TestRegisterInterface.test_port_register_types()
    await TestPersistentMemory.test_persistent_memory()

def run_cyphal_standard_checker():
    asyncio.run(main())


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Cyphal specification checker')
    args = parser.parse_args()
    run_cyphal_standard_checker()
