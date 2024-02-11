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
import time
import can
from enum import Enum
from raccoonlab_tools.common.device_manager import DeviceManager

class ProtocolVerificationError(Exception):
    """Exception raised when the protocol verification fails."""
    pass

class Protocol(Enum):
    UNKNOWN = 0
    CYPHAL = 1
    DRONECAN = 2
    NONE = 3

class TailByte:
    def __init__(self, byte) -> None:
        assert isinstance(byte, int)
        self.byte = byte
        self.sot = self.byte & 128 > 0
        self.eot = self.byte & 64 > 0
        self.toggle = self.byte & 32 > 0
        self.transfer_id = self.byte % 32

    def parse_protocol_from_tail_byte(self) -> Protocol:
        if not self._is_single_frame():
            protocol = Protocol.UNKNOWN
        elif self.toggle:
            protocol = Protocol.CYPHAL
        else:
            protocol = Protocol.DRONECAN
        return protocol

    def __str__(self) -> str:
        return f"[sot={self.sot}, eot={self.eot}, toggle={self.toggle}, transfer_id={self.transfer_id}]"

    def _is_single_frame(self):
        return self.sot and self.eot

class CanMessage:
    def __init__(self, msg : can.message.Message) -> None:
        assert isinstance(msg, can.message.Message)
        self._msg = msg

    def parse_protocol_from_message(self) -> Protocol:
        if len(self._msg.data) != 8:
            return Protocol.UNKNOWN

        tail_byte = TailByte(self._msg.data[7])
        return tail_byte.parse_protocol_from_tail_byte()

    def get_node_id(self) -> int:
        return self._msg.arbitration_id % 128

class CanProtocolParser:
    """
    Static class to find or verify which protocol is used on a given CAN-channel.
    """
    @staticmethod
    def find_protocol(transport=None, verbose=False) -> Protocol:
        """
        Gently try to guess the protocol. Does Not raise an exception.
        """
        assert isinstance(transport, str) or transport is None
        assert isinstance(verbose, bool)

        if transport is None:
            transport = DeviceManager.get_transport(verbose=verbose)

        protocol = CanProtocolParser._parse_protocol(transport)
        if protocol == Protocol.NONE:
            print("[ERROR] CAN-node is offline.")
        elif protocol == Protocol.UNKNOWN:
            print("[ERROR] CAN-node is online, but the protocol couldn't be determined.")
        elif verbose:
            print(f"Found protocol: {protocol}")

        return protocol

    @staticmethod
    def verify_protocol(transport=None, white_list=[Protocol.CYPHAL, Protocol.DRONECAN], verbose=False):
        """
        Return the protocol if it is possible, otherwise rise ProtocolVerificationError exception.
        """
        assert isinstance(transport, str) or transport is None
        assert isinstance(white_list, list)
        assert isinstance(verbose, bool)
        protocol = CanProtocolParser.find_protocol(transport, verbose=True)
        if protocol not in white_list:
            raise ProtocolVerificationError(f"[ERROR] Expected protocols are {white_list}.")

        return protocol

    @staticmethod
    def _parse_protocol(channel : str, time_left : float=1.0):
        """
        Assumptions:
        - If CAN-node exists, it should send at least one 1-byte message within 1 second.
        - Max number of CAN-frames within 1 second is 5000
        """
        if channel.startswith("slcan"):
            config = {"interface": "socketcan", "channel": channel}
        elif channel.startswith("/dev/") or channel.startswith("COM"):
            config = {"interface": "slcan", "channel": channel, "ttyBaudrate": 1000000, "bitrate": 1000000}
        else:
            assert False, f"Unsupported interface {channel}"

        protocol = Protocol.NONE

        with can.Bus(**config) as bus:
            end_time = time.time() + time_left
            while time_left > 0:
                try:
                    can_frame = bus.recv(timeout=time_left)
                except (ValueError, IndexError) as err:
                    print(f"[WARN] CanProtocolParser::_parse_protocol: {err}")

                time_left = end_time - time.time()
                if can_frame is None:
                    continue

                protocol = CanMessage(can_frame).parse_protocol_from_message()
                if protocol is not Protocol.UNKNOWN:
                    break

        return protocol

if __name__ == "__main__":
    transport = DeviceManager.get_transport(verbose=True)
    CanProtocolParser.find_protocol(transport, verbose=True)
