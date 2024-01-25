#!/usr/bin/env python3
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
import can
from enum import Enum

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
    def get_protocol(self):
        if not self.is_single_frame():
            protocol = Protocol.UNKNOWN
        elif self.toggle:
            protocol = Protocol.CYPHAL
        else:
            protocol = Protocol.DRONECAN
        return protocol

class CanMessage:
    def __init__(self, msg) -> None:
        self.msg = msg
        self.tail_byte = TailByte(self.msg.data[7])
    def get_protocol(self):
        return self.tail_byte.get_protocol()
    def get_node_id(self):
        return self.msg.arbitration_id % 128

class CanProtocolParser:
    def __init__(self, channel='/dev/ttyACM0') -> None:
        self.protocol = Protocol.UNKNOWN
        self.node_id = None

        with can.Bus(interface='slcan', channel=channel, ttyBaudrate=1000000, bitrate=1000000) as bus:
            self.protocol = Protocol.UNKNOWN
            for _ in range(100):
                msg = CanMessage(bus.recv())
                self.protocol = msg.get_protocol() if msg is not None else Protocol.UNKNOWN
                self.node_id = msg.get_node_id()
                if self.protocol is not Protocol.UNKNOWN:
                    break

    def get_protocol(self):
        return self.protocol

    def get_node_id(self):
        return self.node_id

if __name__ == "__main__":
    can_protocol_parser = CanProtocolParser()
    print(can_protocol_parser.get_protocol())
