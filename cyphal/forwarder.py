#!/usr/bin/env python3
import asyncio
import sys
import pathlib
import subprocess
from fragments import CyphalFragmentSub, CyphalFragmentPub

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "build/nunavut_out"))
import pycyphal.application
import uavcan.node
import uavcan.node.GetInfo_1_0 as GetInfo_1_0

# RaccoonLab node corresponded registers
UBX_RX_REG = "uavcan.sub.gps.ubx_rx.id"
UBX_TX_REG = "uavcan.pub.gps.ubx_tx.id"


class SerialForwarder:
    def __init__(self, node_id):
        self._ubx_tx_port_id = get_node_register_value(node_id, UBX_TX_REG)
        self._ubx_rx_port_id = get_node_register_value(node_id, UBX_RX_REG)

        print(f" --------------------    -----------------------------    --------------")
        print(f" | forwarder.py     |    | RL GPS_MAG_BARO NODE      |    | UBLOX GNSS |")
        print(f" |              PUB | >> | gps.ubx_rx={self._ubx_rx_port_id :<5}  UART TX | >> | UART RX    |")
        print(f" |              SUB | << | gps.ubx_tx={self._ubx_tx_port_id :<5}  UART RX | << | UART TX    |")
        print(f" --------------------    -----------------------------    --------------")
        print("")

        if self._ubx_tx_port_id == 65535 or self._ubx_rx_port_id == 65535:
            print("Error: required registers are not configured!")
            exit(-1)

    def run(self, commands, send_loop=False, recv_loop=False, verbose=False):
        try:
            asyncio.run(self._main(commands, send_loop, recv_loop, verbose))
        except KeyboardInterrupt:
            pass

    async def _main(self, commands, send_loop, recv_loop, verbose):
        node_info = GetInfo_1_0.Response(
            software_version=uavcan.node.Version_1_0(major=1, minor=0),
            name="ubx"
        )
        self._node = pycyphal.application.make_node(node_info)
        self._node.heartbeat_publisher.mode = uavcan.node.Mode_1_0.OPERATIONAL
        self._node.heartbeat_publisher.vendor_specific_status_code = 50
    
        self._node.start()

        self.ubx_rx_serial_pub = CyphalFragmentPub(self._node, self._ubx_rx_port_id, verbose)
        self.ubx_tx_serial_sub = CyphalFragmentSub(self._node, self._ubx_tx_port_id, verbose)
        self._node.start()

        command_index = 0

        while True:
            await asyncio.sleep(1)

            if send_loop or command_index < len(commands):
                await self.ubx_rx_serial_pub.publish(commands[command_index % len(commands)])
                command_index += 1
            elif recv_loop is False:
                return

def get_node_register_value(node_id, register_name):
    process = subprocess.Popen(f"y r {node_id} {register_name}".split(), stdout=subprocess.PIPE)
    output, _ = process.communicate()
    return int(output)

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Cyphal specification checker')
    parser.add_argument("--verbose", default=False, action='store_true', help="Verbose mode")
    args = parser.parse_args()

    commands = [
        "ubx reset",
        "ubx set baudrate",
        "ubx disable nmea",
        "ubx set required packages",
        "ubx save config"
    ]

    SerialForwarder(node_id=50).run(commands, True, True, verbose=args.verbose)
