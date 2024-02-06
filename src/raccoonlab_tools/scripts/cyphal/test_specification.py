#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
import os
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
from raccoonlab_tools.cyphal.utils import NodeFinder, RegisterInterface, PortRegisterInterface, NodeCommander
from raccoonlab_tools.common.protocol_parser import CanProtocolParser, Protocol
from raccoonlab_tools.common.device_manager import DeviceManager

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
    """
    Let's create a Cyphal node once and reuse it for all tests.
    """
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

@pytest.mark.dependency()
async def test_transport():
    """
    This test is required just for optimization purposes.
    Let's skip all tests if we don't have an online Cyphal node.
    """

    can_iface = os.environ.get('UAVCAN__CAN__IFACE')
    if can_iface is None:
        return  # Skip if transport is not CAN
    if not can_iface.startswith('slcan:'):
        return  # Skip of SocketCAN or other interface

    sniffer_port = can_iface[6:]
    can_protocol_parser = CanProtocolParser(sniffer_port)
    assert can_protocol_parser.get_protocol() == Protocol.CYPHAL


@pytest.mark.asyncio
@pytest.mark.dependency(depends=["test_transport"])
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
@pytest.mark.dependency(depends=["test_transport"])
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
        """Software version field should be filled."""
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
@pytest.mark.dependency(depends=["test_transport"])
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
@pytest.mark.dependency(depends=["test_transport"])
class TestGenericNodeCommands():
    """
    5.3.8. Generic node commands (uavcan.node.ExecuteCommand)
    """


@pytest.mark.asyncio
@pytest.mark.dependency(depends=["test_transport"])
class TestRegisterInterface:
    """5.3.10. Register interface"""
    register_list = []
    access_client = None

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
        required_registers = [
            "uavcan.node.id",
            "uavcan.node.description",
        ]

        register_list = await TestRegisterInterface._collect_register_list()
        assert all(required_register in register_list for required_register in required_registers)

    @staticmethod
    async def test_port_id_register():
        """
        Publication/subscription/client/server port-ID .id registers has the name pattern:
        uavcan.PORT_TYPE.PORT_NAME.id
        Check that they are:
        - natural16[1],
        - mutable,
        - persistent,
        - the default value is 65535.
        """
        register_list = await TestRegisterInterface._collect_register_list()

        for register_name in register_list:
            if PortRegisterInterface.is_port_id(register_name):
                access_response = await TestRegisterInterface._register_access(register_name)
                assert access_response.value.natural16 is not None
                assert access_response._mutable  # pylint: disable=protected-access
                assert access_response.persistent

    @staticmethod
    async def test_port_type_register():
        """
        Publication/subscription/client/server port-ID .type registers has the name pattern:
        uavcan.PORT_TYPE.PORT_NAME.type
        Check that they are:
        - string,
        - immutable,
        - persistent.
        """
        register_list = await TestRegisterInterface._collect_register_list()

        for register_name in register_list:
            if PortRegisterInterface.is_port_type(register_name):
                access_response = await TestRegisterInterface._register_access(register_name)
                assert access_response.value.string is not None
                assert not access_response._mutable  # pylint: disable=protected-access
                assert access_response.persistent

    @staticmethod
    async def test_persistent_memory() -> None:
        """
        Persistent memory check:
        1. set random string parameter to uavcan.node.description (it must exist anyway),
        2. save all parameters to the persistent memory,
        3. reboot the target node,
        4. get uavcan.node.description value
        """
        cyphal_node = GlobalCyphalNode.get_node()
        node_finder = NodeFinder(cyphal_node)
        dest_node_id = await node_finder.find_online_node()
        commander = NodeCommander(cyphal_node, dest_node_id)
        register = "uavcan.node.description"
        random_string = ''.join(random.choices(string.ascii_lowercase, k=10))
        random_value = uavcan.primitive.String_1_0(random_string)

        tested_node_info = await node_finder.get_tested_node_info()
        if tested_node_info['name'] in DEBUGGING_TOOLS_NAME:
            return

        access_response = await TestRegisterInterface._register_access(register, random_value)
        value = "".join([chr(item) for item in access_response.value.string.value])
        assert value == random_string

        await commander.store_persistent_states()

        await commander.restart()

        access_response = await TestRegisterInterface._register_access(register)
        value = "".join([chr(item) for item in access_response.value.string.value])
        assert value == random_string

    @staticmethod
    async def _register_access(register_name, value=None):
        if TestRegisterInterface.access_client is None:
            cyphal_node = GlobalCyphalNode.get_node()
            dest_node_id = await NodeFinder(cyphal_node).find_online_node()
            access_client = cyphal_node.make_client(uavcan.register.Access_1_0, dest_node_id)
            TestRegisterInterface.access_client = access_client

        access_request = uavcan.register.Access_1_0.Request()
        access_request.name.name = register_name

        if isinstance(value, uavcan.primitive.String_1_0):
            access_request.value.string = value

        access_response = await TestRegisterInterface.access_client.call(access_request)
        assert access_response is not None
        access_response = access_response[0]
        return access_response


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

def main():
    import os
    import subprocess
    print(os.path.abspath(__file__))
    subprocess.call(["pytest", os.path.abspath(__file__),
                     "-v",
                     '--asyncio-mode=auto',
                     '-W', 'ignore::DeprecationWarning'])

if __name__ == "__main__":
    main()
