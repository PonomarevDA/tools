#!/usr/bin/env python3
import pycyphal.application
import uavcan.metatransport.serial.Fragment_0_2 as Fragment_0_2

class CyphalFragmentSub:
    def __init__(self, node : pycyphal.application._node_factory.SimpleNode, port_id : int) -> None:
        self._sp_sub = node.make_subscriber(Fragment_0_2, port_id)
        self._sp_sub.receive_in_background(self._sub_cb)
        self._rx_counter = 0
        self._external_callbacks = []

    async def add_callback(self, external_callback):
        self._external_callbacks.append(external_callback)

    async def _sub_cb(self, msg, _):
        # print(len(msg.data), msg.data)
        for external_callback in self._external_callbacks:
            external_callback(msg)

class CyphalFragmentPub:
    def __init__(self, node : pycyphal.application._node_factory.SimpleNode, port_id : int) -> None:
        assert isinstance(port_id, int)
        self._msg = Fragment_0_2()
        self._pub = node.make_publisher(Fragment_0_2, port_id)

    async def publish(self, text):
        self._msg.data = text
        await self._pub.publish(self._msg)
