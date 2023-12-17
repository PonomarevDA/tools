#!/usr/bin/env python3
import asyncio
import sys
import pathlib
import logging
import socket
import numpy

repo_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_dir / "build/nunavut_out"))
sys.path.insert(0, str(repo_dir / "cyphal"))

from fragments import CyphalFragmentSub, CyphalFragmentPub
from utils import CyphalTools
import pycyphal.application
from uavcan.node import GetInfo_1_0


class UbloxCenter:
    """
    -------------       -----------------------
    | U-CENTER  |       | ublox_center.py      |
    |  client   | <<->> | tcp://127.0.0.1:2001 |
    -------------       -----------------------
    """
    def __init__(self, port=2001) -> None:
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', port))
        self.sock.listen(1)
        self.sock.settimeout(5)
        self.client = None
        self.addr = None
        self.buffer = []
        address = f"tcp://127.0.0.1:{port}"
        while True:
            logging.info("Waiting for u-center. Press "
                         "Receiver -> Connection -> Network Connection -> %s",
                         address)
            try:
                self.client, self.addr = self.sock.accept()
                break
            except TimeoutError:
                pass

        self.client.settimeout(0.1)
        logging.info("Connection with u-center established.")

    def send_to_ucenter(self, msg : numpy.ndarray):
        try:
            self.client.send(msg)
            logging.debug("Send to u-center: %s", msg)
        except BrokenPipeError:
            logging.error("BrokenPipeError")
            sys.exit()

    def read_from_ucenter(self):
        msg_from_ucenter = None
        try:
            msg_from_ucenter = self.client.recv(1024)
            logging.debug("Receive from u-center: %s", msg_from_ucenter)
        except TimeoutError:
            pass

        return msg_from_ucenter


class CyphalGnss:
    """
    --------------------     -----------------------------    --------------
    | ublox_center.py  |     | RL GPS_MAG_BARO NODE      |    | UBLOX GNSS |
    |     pub.fragment | >>  | sub.gps.ubx_rx >> UART TX | >> | UART RX    |
    |     sub.fragment | <<  | pub.gps.ubx_tx << UART RX | << | UART TX    |
    --------------------     -----------------------------    --------------
    """
    UBX_RX_REG = "uavcan.sub.gps.ubx_rx.id"
    UBX_TX_REG = "uavcan.pub.gps.ubx_tx.id"
    @staticmethod
    async def create(node, gnss_id):
        fragment_pub_port_id = await CyphalTools.get_port_id_reg_value(gnss_id, CyphalGnss.UBX_RX_REG)
        fragment_sub_port_id = await CyphalTools.get_port_id_reg_value(gnss_id, CyphalGnss.UBX_TX_REG)

        config_required = False
        if fragment_pub_port_id == 65535:
            logging.error("GNSS node: %s is not configured!", CyphalGnss.UBX_RX_REG)
            config_required = True
        if fragment_sub_port_id == 65535:
            logging.error("GNSS node: %s is not configured.", CyphalGnss.UBX_TX_REG)
            config_required = True
        if config_required:
            sys.exit(-1)

        return CyphalGnss(node, fragment_pub_port_id, fragment_sub_port_id)

    def __init__(self, cyphal_node, fragment_pub_port_id : int, fragment_sub_port_id : int) -> None:
        assert isinstance(fragment_pub_port_id, int)
        assert isinstance(fragment_sub_port_id, int)
        self._fragment_pub = CyphalFragmentPub(cyphal_node, fragment_pub_port_id)
        self._fragment_sub = CyphalFragmentSub(cyphal_node, fragment_sub_port_id)

    async def add_callback(self, callback):
        await self._fragment_sub.add_callback(callback)

    async def send(self, msg):
        await self._fragment_pub.publish(msg)


async def main(dest_node_id):
    cyphal_node = pycyphal.application.make_node(GetInfo_1_0.Response(name="ubx"))
    cyphal_node.start()
    logging.debug("Cyphal node created.")

    gnss = await CyphalGnss.create(cyphal_node, dest_node_id)
    ublox_center = UbloxCenter()

    await gnss.add_callback(lambda msg : ublox_center.send_to_ucenter(msg.data))

    while True:
        command_from_ubloc_center = ublox_center.read_from_ucenter()
        if command_from_ubloc_center is not None:
            logging.info("Got command from u-center.")
            await gnss.send(command_from_ubloc_center)
        await asyncio.sleep(1)


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description='U-center over Cyphal')
    parser.add_argument("--verbose", default=False, action='store_true', help="Verbose mode")
    args = parser.parse_args()
    logging.getLogger("pycyphal").setLevel(logging.CRITICAL)
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)
    logging.getLogger().setLevel(logging.DEBUG if args.verbose else logging.INFO)

    try:
        asyncio.run(main(dest_node_id=50))
    except KeyboardInterrupt:
        pass
