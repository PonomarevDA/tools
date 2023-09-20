#!/usr/bin/env python3
import sys
import pathlib

# pylint: disable-next=wrong-import-position
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "build/nunavut_out"))
# pylint: disable=import-error
import uavcan.register.Access_1_0

async def retrive_register_value(cyphal_node, dest_node_id, register_name):
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
