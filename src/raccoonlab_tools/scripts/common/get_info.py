#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import sys
import asyncio
from raccoonlab_tools.common.protocol_parser import CanProtocolParser, Protocol
from raccoonlab_tools.common.device_manager import DeviceManager
from raccoonlab_tools.common.node import NodeInfo

def scan_for_can_sniffer() -> str:
    all_sniffers = DeviceManager().get_all_online_sniffers()
    if len(all_sniffers) == 0:
        print("[ERROR] CAN-sniffer has not been automatically found.")
        sys.exit()
    else:
        print("Found CAN-sniffers:")
        for sniffer in all_sniffers:
            print(f"- {sniffer}")
    return all_sniffers[0].port

def define_can_protocol(sniffer_port : str) -> Protocol:
    assert isinstance(sniffer_port, str)
    protocol_parser = CanProtocolParser(sniffer_port)
    protocol = protocol_parser.get_protocol()
    if protocol == Protocol.UNKNOWN:
        print(f"[ERROR] Found protocol: {protocol}")
        sys.exit()

    print(f"Found protocol: {protocol}")
    return protocol

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

def get_info_dronecan(sniffer_port : str) -> NodeInfo:
    assert isinstance(sniffer_port, str)
    import dronecan
    from raccoonlab_tools.dronecan.utils import NodeFinder

    node = dronecan.make_node(sniffer_port, node_id=100, bitrate=1000000, baudrate=1000000)
    return NodeFinder(node).get_info()

def main():
    sniffer_port = scan_for_can_sniffer()
    can_protocol = define_can_protocol(sniffer_port)
    if can_protocol == Protocol.DRONECAN:
        node_info = get_info_dronecan(sniffer_port)
    elif can_protocol == Protocol.CYPHAL:
        node_info = asyncio.run(get_info_cyphal())
    print(node_info)


if __name__ == "__main__":
    main()
