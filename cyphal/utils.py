#!/usr/bin/env python3
import sys
import time
import pathlib
import asyncio
import numpy

# pylint: disable-next=wrong-import-position
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "build/nunavut_out"))
import pycyphal.application
# pylint: disable=import-error
import uavcan.register.Access_1_0

class CyphalTools:
    cyphal_node = None

    @staticmethod
    async def get_node():
        if CyphalTools.cyphal_node is not None:
            return CyphalTools.cyphal_node

        software_version = uavcan.node.Version_1_0(major=1, minor=0)
        node_info = uavcan.node.GetInfo_1_0.Response(
            software_version,
            name="co.raccoonlab.spec_checker"
        )
        CyphalTools.cyphal_node = pycyphal.application.make_node(node_info)
        CyphalTools.cyphal_node.heartbeat_publisher.mode = uavcan.node.Mode_1_0.OPERATIONAL
        CyphalTools.cyphal_node.start()
        return CyphalTools.cyphal_node

    @staticmethod
    async def find_online_node(timeout : float = 1.1):
        dest_node_id = None
        cyphal_node = await CyphalTools.get_node()

        time_left_sec = timeout
        start_time_sec = time.time()
        sub = cyphal_node.make_subscriber(uavcan.node.Heartbeat_1_0)
        while time_left_sec > 0.0:
            time_left_sec = (start_time_sec + timeout) - time.time()
            transfer = await sub.receive_for(time_left_sec)
            assert isinstance(transfer, tuple), f"Type is type(transfer) :("
            if transfer[1].source_node_id != 127:
                dest_node_id = transfer[1].source_node_id
                break
        sub.close()

        return dest_node_id

    @staticmethod
    async def get_tested_node_name():
        cyphal_node = await CyphalTools.get_node()
        dest_node_id = await CyphalTools.find_online_node()
        request = uavcan.node.GetInfo_1_0.Request()
        client = cyphal_node.make_client(uavcan.node.GetInfo_1_0, dest_node_id)
        response = await client.call(request)
        client.close()
        name = CyphalTools.np_array_to_string(response[0].name)
        return name

    @staticmethod
    async def get_port_list(timeout : float = 10.1) -> None:
        cyphal_node = await CyphalTools.get_node()
        dest_node_id = await CyphalTools.find_online_node()
        msg = None

        time_left_sec = timeout
        start_time_sec = time.time()
        sub = cyphal_node.make_subscriber(uavcan.node.port.List_1_0)
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

    @staticmethod
    def get_port_type_by_register_name(reg : str):
        assert isinstance(reg, str)
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

    @staticmethod
    async def get_port_id_reg_value(dest_node_id : int, register_name : str) -> int:
        assert isinstance(dest_node_id, int)
        assert isinstance(register_name, str)
        cyphal_node = await CyphalTools.get_node()

        access_client = cyphal_node.make_client(uavcan.register.Access_1_0, dest_node_id)

        access_request = uavcan.register.Access_1_0.Request()
        access_request.name.name = register_name

        access_response = await access_client.call(access_request)
        if access_response is None:
            return None # request is not supported or node is not online

        if access_response[0].value.empty is not None:
            return None # register is not exist

        if access_response[0].value.natural16 is None:
            return None # register is not pord.id

        return int(access_response[0].value.natural16.value[0])

    @staticmethod
    def np_array_to_string(np_array : numpy.ndarray) -> str:
        assert isinstance(np_array, numpy.ndarray)
        return "".join([chr(item) for item in np_array])

    @staticmethod
    async def register_list(dest_node_id : int, max_register_amount=256):
        """List registers available on the specified remote node(s)."""
        assert isinstance(dest_node_id, int)
        cyphal_node = await CyphalTools.get_node()

        register_names = []
        list_request = uavcan.register.List_1_0.Request()
        list_client = cyphal_node.make_client(uavcan.register.List_1_0, dest_node_id)
        for _ in range(max_register_amount):
            list_response = await list_client.call(list_request)
            if list_response is None:
                return None

            register_name = CyphalTools.np_array_to_string(list_response[0].name.name)
            if len(register_name) == 0:
                break

            register_names.append(register_name)
            await asyncio.sleep(0.001)
            list_request.index += 1

        return register_names
