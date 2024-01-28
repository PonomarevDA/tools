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

    async def get_tested_node_info(self) -> dict:
        """Return a dictionary on success. Otherwise return None."""
        dest_node_id = await self.find_online_node()

        request = uavcan.node.GetInfo_1_0.Request()
        client = self.node.make_client(uavcan.node.GetInfo_1_0, dest_node_id)
        for attempt in range(3):
            if attempt == 0:
                print(f"NodeInfo: send request to {dest_node_id}")
            else:
                print(f"NodeInfo: send request to {dest_node_id} ({attempt + 1})")
            response = await client.call(request)
            if response is not None:
                break
        client.close()

        if response is not None:
            response = response[0]
            uid_size = 12 if np.all(response.unique_id[12:] == 0) else 16
            uid = ''.join(format(x, '02X') for x in response.unique_id[0:uid_size])
            res = {
                'name'       : _np_array_to_string(response.name),
                'hw_version' : (response.hardware_version.major, response.hardware_version.minor),
                'sw_version' : (response.software_version.major, response.software_version.minor),
                'git_hash'   : response.software_vcs_revision_id,
                'uid'        : uid
            }
        else:
            print(f"Node {dest_node_id} has not respond to NodeInfo request.")
            res = None
        return res

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
                return None

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
        assert isinstance(dest_node_id, int)
        assert isinstance(register_name, str)

        value = await self.registers.register_acess(dest_node_id, register_name)

        if register_name is None or value.natural16 is None:
            return None

        return int(value.natural16.value[0])

    async def set_id(self, dest_node_id : int, register_name : str, value : int) -> int:
        assert isinstance(dest_node_id, int)
        assert isinstance(register_name, str)

        set_value = uavcan.register.Value_1_0(natural16=value)
        read_value = await self.registers.register_acess(dest_node_id, register_name, set_value)

        if register_name is None or read_value.natural16 is None:
            return None

        return int(read_value.natural16.value[0])

    @staticmethod
    def is_port_id(register : str):
        assert isinstance(register, str)
        start_ok = register.startswith(("uavcan.pub", "uavcan.sub", "uavcan.cln", "uavcan.srv"))
        end_ok = register.endswith(".id")
        return start_ok and end_ok

    @staticmethod
    def is_port_type(register : str):
        assert isinstance(register, str)
        start_ok = register.startswith(("uavcan.pub", "uavcan.sub", "uavcan.cln", "uavcan.srv"))
        end_ok = register.endswith(".type")
        return start_ok and end_ok

    @staticmethod
    def get_port_type(port_register_name : str):
        assert isinstance(port_register_name, str)
        port_type = None
        port_reg_type = None

        if port_register_name.startswith("uavcan.pub"):
            port_type = 'pub'
        elif port_register_name.startswith("uavcan.sub"):
            port_type = 'sub'
        elif port_register_name.startswith("uavcan.cln"):
            port_type = 'cln'
        elif port_register_name.startswith("uavcan.srv"):
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
