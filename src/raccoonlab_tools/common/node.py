#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
from dataclasses import dataclass
from binascii import hexlify
from raccoonlab_tools.common.colorizer import Colors

@dataclass
class SoftwareVersion:
    major : int = 0
    minor : int = 0
    vcs_commit : str = "BADC0FFEE"
    image_crc : int = 0

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}_{self.vcs_commit}"

@dataclass
class HardwareVersion:
    major : int = 0
    minor : int = 0
    unique_id : str = ""
    coa : int = 0

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}"

@dataclass
class NodeInfo:
    """
    This is protocol abstract Node Info
    """
    node_id : int
    name : str
    software_version : SoftwareVersion = SoftwareVersion()
    hardware_version : HardwareVersion = HardwareVersion()

    @staticmethod
    def create_from_cyphal_response(transfer : tuple):
        assert isinstance(transfer, tuple) or len(transfer) != 2

        response = transfer[0]
        transfer_from = transfer[1]
        node_info = NodeInfo(
            node_id=transfer_from.source_node_id,
            name=''.join(map(chr, response.name)),
            software_version=SoftwareVersion(
                response.software_version.major,
                response.software_version.minor,
                hex(response.software_vcs_revision_id)[2:]
            ),
            hardware_version=HardwareVersion(
                response.hardware_version.major,
                response.hardware_version.minor,
                hexlify(bytes(response.unique_id)).decode('utf-8')
            )
        )
        return node_info

    @staticmethod
    def create_from_dronecan_get_info_response(transfer):
        """Transfer has type dronecan.node.TransferEvent"""
        node_info = NodeInfo(
            node_id=transfer.transfer.source_node_id,
            name=''.join(map(chr, transfer.response.name)),
            software_version=SoftwareVersion(
                transfer.response.software_version.major,
                transfer.response.software_version.minor,
                hex(transfer.response.software_version.vcs_commit)[2:]
            ),
            hardware_version=HardwareVersion(
                transfer.response.hardware_version.major,
                transfer.response.hardware_version.minor,
                hexlify(bytes(transfer.response.hardware_version.unique_id)).decode('utf-8')
            )
        )
        return node_info

    def print_info(self, latest_sw_version : str) -> None:
        assert isinstance(latest_sw_version, str)

        print("Node info:")
        print(f"- Name: {self.name}")

        print(f"- SW: ", end='')
        if len(latest_sw_version) == 0:
            print(f"{self.software_version} (SW history is unknown)")
        elif self.software_version.vcs_commit == latest_sw_version:
            print(f"{self.software_version} (latest)")
        else:
            print((f"{Colors.FAIL}{self.software_version}"
                   f"(need update: latest is {latest_sw_version}){Colors.ENDC}"))

        print(f"- HW: {self.hardware_version}")
        print(f"- ID: {self.node_id}")
        print(f"- UID: {self.hardware_version.unique_id}")
