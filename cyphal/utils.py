#!/usr/bin/env python3
import sys
import pathlib
import asyncio

# pylint: disable-next=wrong-import-position
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "build/nunavut_out"))
# pylint: disable=import-error
import uavcan.register.Access_1_0

async def get_port_id_reg_value(cyphal_node, dest_node_id, register_name):
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

    return access_response[0].value.natural16.value[0]

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
