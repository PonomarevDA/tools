#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import time
import asyncio
import numpy as np

# pylint: disable=import-error
import uavcan.register.Access_1_0
import uavcan.register.List_1_0
import uavcan.register.Name_1_0
import uavcan.register.Value_1_0
import uavcan.node.port.List_1_0

from raccoonlab_tools.common.node import NodeInfo

UAVCAN_PUB = "uavcan.pub"
UAVCAN_SUB = "uavcan.sub"
UAVCAN_CLN = "uavcan.cln"
UAVCAN_SRV = "uavcan.srv"

class NodeFinder:
    """
    This class performs a network scan for a target node and collects a basic information.
    Possible target nodes id are [0, 126].
    Node ID 127 is intentionally ignored because it is usually occupied by debugging tools.
    """
    target_node_id = None
    black_list = [127]

    def __init__(self, cyphal_node) -> None:
        self.node = cyphal_node

    async def find_online_node(self, timeout : float = 1.1) -> int:
        assert isinstance(timeout, float)

        if NodeFinder.target_node_id is not None:
            return NodeFinder.target_node_id

        time_left_sec = timeout
        start_time_sec = time.time()
        sub = self.node.make_subscriber(uavcan.node.Heartbeat_1_0)
        while time_left_sec > 0.0:
            time_left_sec = (start_time_sec + timeout) - time.time()
            transfer = await sub.receive_for(time_left_sec)
            if transfer is None:
                break
            assert isinstance(transfer, tuple), "Type is type(transfer) :("
            if transfer[1].source_node_id not in NodeFinder.black_list:
                NodeFinder.target_node_id = transfer[1].source_node_id
                break
        sub.close()

        return NodeFinder.target_node_id

    async def get_info(self) -> dict:
        """Return a dictionary on success. Otherwise return None."""
        dest_node_id = await self.find_online_node()

        request = uavcan.node.GetInfo_1_0.Request()
        client = self.node.make_client(uavcan.node.GetInfo_1_0, dest_node_id)
        for attempt in range(3):
            if attempt == 0:
                print(f"[DEBUG] NodeInfo: send request to {dest_node_id}")
            else:
                print(f"[DEBUG] NodeInfo: send request to {dest_node_id} ({attempt + 1})")
            response = await client.call(request)
            if response is not None:
                break
        client.close()

        if response is not None:
            node_info = NodeInfo.create_from_cyphal_response(response)
        else:
            print(f"[WARN] Node {dest_node_id} has not respond to NodeInfo request.")
            node_info = None
        return node_info

    async def get_port_list(self, timeout : float = 10.1) -> uavcan.node.port.List_1_0:
        dest_node_id = await self.find_online_node()
        msg = None

        time_left_sec = timeout
        start_time_sec = time.time()
        sub = self.node.make_subscriber(uavcan.node.port.List_1_0)
        while time_left_sec > 0.0:
            time_left_sec = (start_time_sec + timeout) - time.time()
            transfer = await sub.receive_for(time_left_sec)
            assert isinstance(transfer, tuple)
            transfer_from = transfer[1]
            if transfer_from.source_node_id == dest_node_id:
                msg = transfer[0]
                break
        sub.close()

        assert isinstance(msg, uavcan.node.port.List_1_0)
        return msg


class RegisterInterface:
    """
    This class simplifies the operations with Cyphal registers.
    It basically just a wrapper under:
    - uavcan.register.Access_1_0
    - uavcan.register.List_1_0
    """

    def __init__(self, cyphal_node) -> None:
        self.node = cyphal_node

    async def register_list(self, dest_node_id : int, max_register_amount=256) -> list:
        """
        List registers available on the specified remote node.
        Simplied version of `yakut register-list`.
        Return a list of strings with names of all avaliable registers.
        """
        assert isinstance(dest_node_id, int)

        register_names = []
        list_request = uavcan.register.List_1_0.Request()
        list_client = self.node.make_client(uavcan.register.List_1_0, dest_node_id)
        for _ in range(max_register_amount):
            list_response = await list_client.call(list_request)
            if list_response is None:
                break

            register_name = _np_array_to_string(list_response[0].name.name)
            if len(register_name) == 0:
                break

            register_names.append(register_name)
            await asyncio.sleep(0.001)
            list_request.index += 1

        return register_names

    async def register_acess(self, dest_node_id : int, register_name : str, value=None) -> list:
        """
        Read or modify a register on a remote node.
        Simplied version of `yakut register-access`.
        Return None or uavcan.register.Value_1_0.
        """
        assert isinstance(dest_node_id, int)
        assert isinstance(register_name, str)
        client = self.node.make_client(uavcan.register.Access_1_0, dest_node_id)
        request = uavcan.register.Access_1_0.Request(name=uavcan.register.Name_1_0(register_name))
        if value is not None:
            request.value = value

        response = await client.call(request)
        if response is None:
            return None # request is not supported or the node is offline

        return response[0].value


class PortRegisterInterface:
    """
    This class simplifies port identifier reading and configuration
    """
    def __init__(self, cyphal_node) -> None:
        self.node = cyphal_node
        self.registers = RegisterInterface(self.node)

    async def get_id(self, dest_node_id : int, register_name : str) -> int:
        assert isinstance(dest_node_id, int) and dest_node_id >= 1 and dest_node_id <= 127
        assert isinstance(register_name, str)

        read_value = await self.registers.register_acess(dest_node_id, register_name)

        if read_value is None:
            print(f"[WARN] Register {register_name} has not been responded")
            return None

        if read_value.natural16 is None:
            print(f"[ERROR] Register {register_name} is not natural16")
            return None

        return int(read_value.natural16.value[0])

    async def set_id(self, dest_node_id : int, register_name : str, value : int) -> int:
        assert isinstance(dest_node_id, int) and dest_node_id >= 1 and dest_node_id <= 127
        assert isinstance(register_name, str)
        assert isinstance(value, int) and value >= 1 and value <= 65535

        set_value = uavcan.register.Value_1_0(natural16=uavcan.primitive.array.Natural16_1_0(value))
        read_value = await self.registers.register_acess(dest_node_id, register_name, set_value)

        if read_value is None:
            print(f"[WARN] Register {register_name} has not been responded")
            return None

        if read_value.natural16 is None:
            print(f"[ERROR] Register {register_name} is not natural16")
            return None

        return int(read_value.natural16.value[0])

    @staticmethod
    def is_port_id(register : str):
        assert isinstance(register, str)
        start_ok = register.startswith((UAVCAN_PUB, UAVCAN_SUB, UAVCAN_CLN, UAVCAN_SRV))
        end_ok = register.endswith(".id")
        return start_ok and end_ok

    @staticmethod
    def is_port_type(register : str):
        assert isinstance(register, str)
        start_ok = register.startswith((UAVCAN_PUB, UAVCAN_SUB, UAVCAN_CLN, UAVCAN_SRV))
        end_ok = register.endswith(".type")
        return start_ok and end_ok

    @staticmethod
    def get_port_type(port_register_name : str):
        assert isinstance(port_register_name, str)
        port_type = None
        port_reg_type = None

        if port_register_name.startswith(UAVCAN_PUB):
            port_type = 'pub'
        elif port_register_name.startswith(UAVCAN_SUB):
            port_type = 'sub'
        elif port_register_name.startswith(UAVCAN_CLN):
            port_type = 'cln'
        elif port_register_name.startswith(UAVCAN_SRV):
            port_type = 'srv'

        if port_register_name.endswith(".id"):
            port_reg_type = "id"
        elif port_register_name.endswith(".type"):
            port_reg_type = "type"

        return port_type, port_reg_type


class NodeCommander:
    """
    Wrapper under ExecuteCommand
    """
    def __init__(self, cyphal_node, dest_node_id) -> None:
        self.node = cyphal_node
        self.cmd_client = None
        self.dest_node_id = dest_node_id
        self.cmd_client = self.node.make_client(uavcan.node.ExecuteCommand_1_1, dest_node_id)

    async def store_persistent_states(self):
        save_request = uavcan.node.ExecuteCommand_1_1.Request(command = 65530)
        cmd_response = await self.cmd_client.call(save_request)
        assert cmd_response is not None

    async def restart(self):
        save_request = uavcan.node.ExecuteCommand_1_1.Request(command = 65535)
        await self.cmd_client.call(save_request)

def _np_array_to_string(np_array : np.ndarray) -> str:
    assert isinstance(np_array, np.ndarray)
    return "".join([chr(item) for item in np_array])
