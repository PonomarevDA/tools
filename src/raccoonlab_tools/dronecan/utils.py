#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import dronecan
from typing import Union
from dataclasses import dataclass
from raccoonlab_tools.common.node import NodeInfo

@dataclass
class Parameter:
    name: str
    value : Union[None, str, int, float]
    min_value : Union[None, int, float] = None
    max_value : Union[None, int, float] = None
    def_value : Union[None, str, int, float] = None

    def __str__(self) -> str:
        return f"{self.name :<30}: {self.value}"

    def create_getset_request(self) -> dronecan.uavcan.protocol.param.GetSet.Request:
        req = dronecan.uavcan.protocol.param.GetSet.Request()
        req.name = self.name
        if isinstance(self.value, int):
            req.value.integer_value = self.value
        elif isinstance(self.value, str):
            req.value.string_value = self.value
        return req


class ParametersInterface:
    """
    A simple wrapper under uavcan.protocol.param.GetSet.
    """
    def __init__(self, node : dronecan.node.Node, target_node_id : int) -> None:
        assert isinstance(node, dronecan.node.Node)
        assert isinstance(target_node_id, int)
        self.node = node
        self._target_node_id = target_node_id
        self._parameter = None

    def get(self, idx : int) -> Parameter:
        """
        None means that the target node dodn't respond
        Empty means the parameter doesn't exist.
        """
        assert isinstance(idx, int)
        req = dronecan.uavcan.protocol.param.GetSet.Request(index=idx)
        self._parameter = None
        self.node.request(req, self._target_node_id, self._callback)
        for _ in range(20):
            self.node.spin(0.005)
            if self._parameter is not None:
                break

        return self._parameter

    def get_all(self) -> list:
        all_params = []
        for idx in range(255):
            parameter = self.get(idx)
            if parameter is None or parameter.value is None:
                break
            all_params.append(parameter)
        return all_params

    def set(self, param : Parameter) -> Parameter:
        """
        None means that the target node dodn't respond
        Empty means the parameter doesn't exist.
        """
        assert isinstance(param, Parameter)
        self._parameter = None
        self.node.request(param.create_getset_request(), self._target_node_id, self._callback)
        for _ in range(20):
            self.node.spin(0.005)
            if self._parameter is not None:
                break

        return self._parameter

    def _callback(self, msg : dronecan.uavcan.protocol.param.GetSet.Response):
        if hasattr(msg.response.value, 'boolean_value'):
            value = bool(msg.response.value.boolean_value)
        elif hasattr(msg.response.value, 'integer_value'):
            value = int(msg.response.value.integer_value)
        elif hasattr(msg.response.value, 'real_value'):
            value = float(msg.response.value.real_value)
        elif hasattr(msg.response.value, 'string_value'):
            string = msg.response.value.string_value
            value = str(string) if len(string) > 0 and string[0] != 255 else ""
        else:
            value = None

        self._parameter = Parameter(
            name = str(msg.response.name),
            value = value
        )

class NodeFinder:
    """
    Sscan a network for a target node.
    Possible target nodes id are [0, 126].
    Node ID 127 is intentionally ignored because it is usually occupied by debugging tools.
    """
    node_id = None
    black_list = [127]

    def __init__(self, dronecan_node : dronecan.node.Node) -> None:
        self._node = dronecan_node
        self._response = None

    def find_online_node(self, time_left_sec : float = 1.1) -> int:
        assert isinstance(time_left_sec, float)

        if NodeFinder.node_id is not None:
            return NodeFinder.node_id

        handler = self._node.add_handler(dronecan.uavcan.protocol.NodeStatus, self._node_status_cb)
        while time_left_sec > 0.0:
            time_left_sec -= 0.005
            self._node.spin(0.005)
            if NodeFinder.node_id is not None:
                break
        handler.remove()

        return NodeFinder.node_id

    def get_info(self) -> NodeInfo:
        node_id = self.find_online_node()
        assert node_id >= 1 and node_id <= 127

        self._response = None
        get_node_info_request = dronecan.uavcan.protocol.GetNodeInfo.Request()
        self._node.request(get_node_info_request, node_id, self._node_info_response_cb)
        for _ in range(20):
            self._node.spin(0.005)
            if self._response is not None:
                return NodeInfo.create_from_dronecan_get_info_response(self._response)

        return None

    def _node_status_cb(self, transfer : dronecan.node.TransferEvent):
        source_node_id = transfer.transfer.source_node_id
        if source_node_id not in NodeFinder.black_list:
            NodeFinder.node_id = source_node_id

    def _node_info_response_cb(self, transfer):
        self._response = transfer

class NodeCommander:
    """
    Wrapper under ExecuteCommand
    """
    def __init__(self, node, target_node_id) -> None:
        self.node = node
        self.dest_node_id = target_node_id
        self._stored = False
        self._restarted = False

    def store_persistent_states(self):
        req = dronecan.uavcan.protocol.param.ExecuteOpcode.Request(opcode=1)
        self.node.request(req, self.dest_node_id, self._execute_opcode_response_cb)
        self._stored = None
        for _ in range(20):
            self.node.spin(0.005)
            if self._stored is not None:
                break
        return self._stored

    def restart(self):
        req = dronecan.uavcan.protocol.RestartNode.Request(magic_number=0xACCE551B1E)
        self.node.request(req, self.dest_node_id, self._restart_node_response_cb)
        self._restarted = None
        for _ in range(20):
            self.node.spin(0.005)
            if self._restarted is not None:
                break
        return self._restarted

    def _execute_opcode_response_cb(self, transfer_event):
        assert isinstance(transfer_event, dronecan.node.TransferEvent)
        self._stored = transfer_event.transfer.payload.ok

    def _restart_node_response_cb(self, transfer_event):
        assert isinstance(transfer_event, dronecan.node.TransferEvent)
        self._restarted = transfer_event.transfer.payload.ok


# Tests
if __name__ =="__main__":
    node = dronecan.make_node('slcan:/dev/ttyACM0', node_id=100, bitrate=1000000, baudrate=1000000)

    target_node_finder = NodeFinder(node)
    target_node_id = target_node_finder.find_online_node()

    params_interface = ParametersInterface(node=node, target_node_id=target_node_id)
    all_params = params_interface.get_all()
    for param in all_params:
        print(param)

