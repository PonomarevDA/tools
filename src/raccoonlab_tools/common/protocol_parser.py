#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

"""
Cyphal tail byte:
Bit     Field               Single-frame        Multi-frame transfers
7       Start of transfer   Always 1            First frame: 1, otherwise 0
6       End of transfer     Always 1            Last frame: 1, otherwise 0
5       Toggle bit          Always 1            First frame: 1, then alternates
0-4     Transfer-ID         range [0, 31]       range [0, 31]

DroneCAN tail byte:
Bit     Field               Single-frame        Multi-frame transfers
7       Start of transfer   Always 1            First frame: 1, otherwise 0
6       End of transfer     Always 1            Last frame: 1, otherwise 0
5       Toggle bit          Always 0            First frame: 0, then alternates
0-4     Transfer-ID         range [0, 31]       range [0, 31]
"""
import sys
import can
from enum import Enum
from raccoonlab_tools.common.device_manager import DeviceManager

class Protocol(Enum):
    UNKNOWN = 0
    CYPHAL = 1
    DRONECAN = 2

class TailByte:
    def __init__(self, byte) -> None:
        assert isinstance(byte, int)
        self.byte = byte
        self.sot = self.byte & 128 > 0
        self.eot = self.byte & 64 > 0
        self.toggle = self.byte & 32 > 0
        self.transfer_id = self.byte % 32
    def __str__(self) -> str:
        return f"[sot={self.sot}, eot={self.eot}, toggle={self.toggle}, transfer_id={self.transfer_id}]"
    def is_single_frame(self):
        return self.sot and self.eot
    def parse_protocol_from_tail_byte(self):
        if not self.is_single_frame():
            protocol = Protocol.UNKNOWN
        elif self.toggle:
            protocol = Protocol.CYPHAL
        else:
            protocol = Protocol.DRONECAN
        return protocol

class CanMessage:
    def __init__(self, msg) -> None:
        self._msg = msg
        self._tail_byte = TailByte(self._msg.data[7])
    def parse_protocol_from_message(self):
        return self._tail_byte.parse_protocol_from_tail_byte()
    def get_node_id(self):
        return self._msg.arbitration_id % 128

class CanProtocolParser:
    def __init__(self, channel : str) -> None:
        assert isinstance(channel, str)
        self.protocol = Protocol.UNKNOWN
        self.node_id = None

        with can.Bus(interface='slcan', channel=channel, ttyBaudrate=1000000, bitrate=1000000) as bus:
            self.protocol = Protocol.UNKNOWN
            for _ in range(100):
                try:
                    can_frame = bus.recv()
                except (ValueError, IndexError) as err:
                    print(f"[WARN] {err}")
                    continue

                if len(can_frame.data) != 8:
                    continue
                msg = CanMessage(can_frame)
                self.protocol = msg.parse_protocol_from_message()
                self.node_id = msg.get_node_id()
                if self.protocol is not Protocol.UNKNOWN:
                    break

    @staticmethod
    def find_protocol(sniffer=None, verbose=False) -> Protocol:
        """ Gently try to guess the protocol. Does Not raise an exception."""
        assert isinstance(sniffer, str) or sniffer is None
        assert isinstance(verbose, bool)

        if sniffer is None:
            sniffer = DeviceManager.get_sniffer(verbose=verbose)

        parser = CanProtocolParser(sniffer)
        if parser.protocol == Protocol.UNKNOWN:
            print(f"[ERROR] Neither Cyphal or DroneCAN protocol can be automatically determined.")
        elif verbose:
            print(f"Found protocol: {parser.protocol}")

        return parser.protocol

    @staticmethod
    def verify_protocol(sniffer=None, white_list=[Protocol.CYPHAL, Protocol.DRONECAN], verbose=False):
        """ Return the protocol if it is possible, otherwise rise an exception."""
        assert isinstance(sniffer, str) or sniffer is None
        assert isinstance(white_list, list)
        assert isinstance(verbose, bool)
        protocol = CanProtocolParser.find_protocol(sniffer, verbose=True)
        if protocol not in white_list:
            raise Exception(f"[ERROR] Expected protocols are {white_list}.")

        return protocol

    def get_node_id(self):
        return self.node_id

if __name__ == "__main__":
    sniffer = DeviceManager.get_sniffer(verbose=True)
    CanProtocolParser.find_protocol(sniffer, verbose=True)
