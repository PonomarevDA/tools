#!/usr/bin/env python3
import asyncio
import sys
import pathlib
import subprocess
import logging
import numpy
import socket

repo_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_dir / "build/nunavut_out"))
sys.path.insert(0, str(repo_dir / "cyphal"))

from fragments import CyphalFragmentSub, CyphalFragmentPub
import pycyphal.application
import uavcan.node
import uavcan.node.GetInfo_1_0 as GetInfo_1_0


# RaccoonLab node corresponded registers
UBX_RX_REG = "uavcan.sub.gps.ubx_rx.id"
UBX_TX_REG = "uavcan.pub.gps.ubx_tx.id"


class UbloxCenterInterface:
    def __init__(self, port=2001) -> None:
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', port))
        self.sock.listen(1)
        self.client = None
        self.addr = None
        self.buffer = []
        logging.info("Press Receiver -> Connection -> Network Connection -> `tcp://127.0.0.1:2001` ...")
        while True:
            self.client, self.addr = self.sock.accept()
            break

        self.client.settimeout(0.1)
        logging.debug("Connection with u-center established.")

    def send_to_ucenter(self, msg : numpy.ndarray):
        try:
            self.client.send(msg)
            logging.debug(f"Send to u-center: {msg}")
        except BrokenPipeError:
            logging.error("BrokenPipeError")
            sys.exit()

    def read_from_ucenter(self):
        msg_from_ucenter = None
        try:
            msg_from_ucenter = self.client.recv(1024)
            logging.debug(f"Receive from u-center: {msg_from_ucenter}")
        except TimeoutError:
            pass

        return msg_from_ucenter


class UbloxCenter:
    def __init__(self, node_id):
        self._fragment_pub_port_id = get_node_register_value(node_id, UBX_RX_REG)
        self._fragment_sub_port_id = get_node_register_value(node_id, UBX_TX_REG)
        self.ublox_center = UbloxCenterInterface()

        print("")
        print(f" --------------------    -----------------------------    --------------")
        print(f" | forwarder.py     |    | RL GPS_MAG_BARO NODE      |    | UBLOX GNSS |")
        print(f" |              PUB | >> | gps.ubx_rx={self._fragment_pub_port_id :<5}  UART TX | >> | UART RX    |")
        print(f" |              SUB | << | gps.ubx_tx={self._fragment_sub_port_id :<5}  UART RX | << | UART TX    |")
        print(f" --------------------    -----------------------------    --------------")
        print("")

        if self._fragment_sub_port_id == 65535 or self._fragment_pub_port_id == 65535:
            logging.error("Required registers are not configured!")
            exit(-1)

    def run(self):
        try:
            asyncio.run(self._main())
        except KeyboardInterrupt:
            pass

    async def _main(self):
        node_info = GetInfo_1_0.Response(
            software_version=uavcan.node.Version_1_0(major=1, minor=0),
            name="ubx"
        )
        self._node = pycyphal.application.make_node(node_info)
        self._node.heartbeat_publisher.mode = uavcan.node.Mode_1_0.OPERATIONAL
        self._node.heartbeat_publisher.vendor_specific_status_code = 50
    
        self._node.start()

        self.fragment_pub = CyphalFragmentPub(self._node, self._fragment_pub_port_id)
        self.fragment_sub = CyphalFragmentSub(self._node, self._fragment_sub_port_id)
        
        await self.fragment_sub.add_callback(lambda msg : self.ublox_center.send_to_ucenter(msg.data))
        
        while True:
            self.ublox_center.read_from_ucenter()
            await asyncio.sleep(1)

def get_node_register_value(node_id, register_name):
    process = subprocess.Popen(f"y r {node_id} {register_name}".split(), stdout=subprocess.PIPE)
    output, _ = process.communicate()
    return int(output)


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description='U-center over Cyphal/CAN')
    parser.add_argument("--verbose", default=False, action='store_true', help="Verbose mode")
    args = parser.parse_args()
    logging.getLogger("pycyphal").setLevel(logging.CRITICAL)
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)
    logging.getLogger().setLevel(logging.DEBUG if args.verbose else logging.INFO)

    UbloxCenter(node_id=50).run()
