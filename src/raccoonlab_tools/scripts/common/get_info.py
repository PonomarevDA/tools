#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import asyncio
from raccoonlab_tools.common.protocol_parser import CanProtocolParser, Protocol
from raccoonlab_tools.common.device_manager import DeviceManager
from raccoonlab_tools.common.node import NodeInfo

async def get_info_cyphal() -> NodeInfo:
    import pycyphal
    import pycyphal.application
    import uavcan
    from raccoonlab_tools.cyphal.utils import NodeFinder

    get_info_response = uavcan.node.GetInfo_1_0.Response(
        uavcan.node.Version_1_0(major=1, minor=0),
        name="co.raccoonlab.spec_checker"
    )
    cyphal_node = pycyphal.application.make_node(get_info_response)
    cyphal_node.start()
    node_info = await NodeFinder(cyphal_node).get_info()
    return node_info

def get_info_dronecan(transport : str) -> NodeInfo:
    assert isinstance(transport, str)
    import dronecan
    from raccoonlab_tools.dronecan.utils import NodeFinder

    node = dronecan.make_node(transport, node_id=100, bitrate=1000000, baudrate=1000000)
    return NodeFinder(node).get_info()

def main():
    transport = DeviceManager.get_transport(verbose=True)
    can_protocol = CanProtocolParser.verify_protocol(transport, verbose=True)
    if can_protocol == Protocol.DRONECAN:
        node_info = get_info_dronecan(transport)
    elif can_protocol == Protocol.CYPHAL:
        node_info = asyncio.run(get_info_cyphal())
    node_info.print_info("")


if __name__ == "__main__":
    main()
