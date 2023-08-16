#!/usr/bin/env python3
import asyncio
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "compile_output"))
import pycyphal.application
import uavcan.node
import uavcan.node.GetInfo_1_0 as GetInfo_1_0
import uavcan.metatransport.serial.Fragment_0_2 as Fragment_0_2

class UbxTxFragmentSub:
    def __init__(self, node, port_id) -> None:
        node.registry["uavcan.sub.ubx_tx.id"] = port_id
        self._sp_sub = node.make_subscriber(Fragment_0_2, "ubx_tx")
        self._sp_sub.receive_in_background(self._sub_cb)
        self._rx_counter = 0

    async def _sub_cb(self, msg, _, chunk_size=22):
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

class UbxRxFragmentPub:
    def __init__(self, node, port_id) -> None:
        node.registry["uavcan.pub.ubx_rx.id"] = port_id
        self._msg = Fragment_0_2()
        self._pub = node.make_publisher(Fragment_0_2, "ubx_rx")

    async def publish(self, text):
        self._msg.data = text
        await self._pub.publish(self._msg)

class SerialForwarder:
    def __init__(self, ubx_rx_port_id, ubx_tx_port_id):
        self._ubx_rx_port_id = ubx_rx_port_id
        self._ubx_tx_port_id = ubx_tx_port_id

    def run(self, commands, loop=False):
        asyncio.run(self._main(commands, loop))

    async def _main(self, commands, loop):
        node_info = GetInfo_1_0.Response(
            software_version=uavcan.node.Version_1_0(major=1, minor=0),
            name="ubx"
        )
        self._node = pycyphal.application.make_node(node_info)
        self._node.heartbeat_publisher.mode = uavcan.node.Mode_1_0.OPERATIONAL
        self._node.heartbeat_publisher.vendor_specific_status_code = 50
        self._node.start()

        self.ubx_rx_serial_pub = UbxRxFragmentPub(self._node, self._ubx_rx_port_id)
        self.ubx_tx_serial_sub = UbxTxFragmentSub(self._node, self._ubx_tx_port_id)

        command_index = 0

        while True:
            await asyncio.sleep(1)

            if loop or command_index < len(commands):
                await self.ubx_rx_serial_pub.publish(commands[command_index % len(commands)])
                command_index += 1

if __name__ == "__main__":
    commands = [
        "ubx reset!",
        "ubx set baudrate!",
        "ubx disable nmea!",
        "ubx set required packages!",
        "ubx save config!"
    ]

    SerialForwarder(3500, 3501).run(commands)
