#!/usr/bin/env python3
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "build/nunavut_out"))
import pycyphal.application
import uavcan.metatransport.serial.Fragment_0_2 as Fragment_0_2

class CyphalFragmentSub:
    def __init__(self, node : pycyphal.application._node_factory.SimpleNode, port_id : int, verbose : bool) -> None:
        self._sp_sub = node.make_subscriber(Fragment_0_2, port_id)
        self._sp_sub.receive_in_background(self._sub_cb)
        self._rx_counter = 0
        self._verbose = verbose
        self._external_callbacks = []

    async def add_callback(self, external_callback):
        self._external_callbacks.append(external_callback)

    async def _sub_cb(self, msg, _):
        for external_callback in self._external_callbacks:
            external_callback(msg)

        if self._verbose:
            await self._print(msg)

    async def _print(self, msg, chunk_size=22):
        total_size = len(msg.data.tobytes())
        for first_index in range(0, total_size, chunk_size):
            last_index = first_index + min(total_size - first_index, chunk_size)
            length = last_index - first_index
            print(f"RX[{length : < 3}] ", end ="")
            for idx in range(first_index, last_index):
                if msg.data[idx] == 181:
                    byte_str = f"\033[93m{msg.data[idx]}\033[0m"
                elif msg.data[idx] == 98:
                    byte_str = f"\033[95m{msg.data[idx]}\033[0m"
                else:
                    byte_str = msg.data[idx]

                print(byte_str, end =" ")
            print("")
            self._rx_counter += length

class CyphalFragmentPub:
    def __init__(self, node : pycyphal.application._node_factory.SimpleNode, port_id : int, verbose : bool) -> None:
        self._msg = Fragment_0_2()
        self._pub = node.make_publisher(Fragment_0_2, port_id)
        self._verbose = verbose

    async def publish(self, text):
        self._msg.data = text
        if self._verbose:
            print(f"TX[{len(text) : < 3}] {text}")
        await self._pub.publish(self._msg)
