#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import dronecan
from typing import Union
from dataclasses import dataclass

@dataclass
class Parameter:
    name: str
    value : Union[None, str, int, float]
    min_value : Union[None, int, float] = None
    max_value : Union[None, int, float] = None
    def_value : Union[None, str, int, float] = None

    def __str__(self) -> str:
        return f"{self.name :<30}: {self.value}"


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
        Empty means the paramter doesn't exist.
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


# Tests
if __name__ =="__main__":
    node = dronecan.make_node('slcan:/dev/ttyACM0', node_id=100, bitrate=1000000, baudrate=1000000)
    params_interface = ParametersInterface(node=node, target_node_id=32)
    all_params = params_interface.get_all()
    for param in all_params:
        print(param)

