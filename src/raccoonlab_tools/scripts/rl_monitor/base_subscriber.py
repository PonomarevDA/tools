#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import time
import numpy
import copy
import pycyphal.application
from raccoonlab_tools.common.colorizer import Colors
from raccoonlab_tools.cyphal.utils import PortRegisterInterface

class RateEstimator:
    def __init__(self, window_size_sec=1.0) -> None:
        self._timestamps = []
        self._window_size_sec = window_size_sec

    def register_message(self):
        self._update_timestamps()
        self._timestamps.append(time.time())

    def get_rate(self) -> int:
        self._update_timestamps()
        return int(len(self._timestamps) / self._window_size_sec)

    def _update_timestamps(self):
        deadline = time.time() - self._window_size_sec
        self._timestamps = [timestamp for timestamp in self._timestamps if timestamp > deadline]


class BaseSubscriber:
    def __init__(self,
                 node : pycyphal.application._node_factory.SimpleNode,
                 node_id : int,
                 def_id : int,
                 reg_name : str,
                 data_type) -> None:
        assert isinstance(node, pycyphal.application._node_factory.SimpleNode)
        assert isinstance(node_id, int)
        assert isinstance(def_id, int)
        assert isinstance(reg_name, str) or isinstance(reg_name, tuple)
        self.node = node
        self.data = None
        self._id = None
        self.id_updated = False
        self.node_id = node_id
        self.def_id = def_id
        self.reg_names = reg_name if isinstance(reg_name, tuple) else (reg_name, )
        self.data_type = data_type
        self.port_interface = PortRegisterInterface(self.node)
        self._msg_counter = 0
        self._rate_estiamtor = RateEstimator(window_size_sec=2.0)
        self.min = None
        self.max = None

    async def init_sub(self):
        for reg_name in self.reg_names:
            self._id = await self.port_interface.get_id(self.node_id, reg_name)
            print(f"y r {self.node_id} {reg_name} # {self._id}")
            if self._id is not None:
                break
        if self._id is None:
            print(f"[WARN] {self.reg_names} is not exist")
            return

        self.id_updated = (self._id == 0) or (self._id > 8191)

        if self.id_updated:
            self._id = await self.port_interface.set_id(self.node_id, reg_name, self.def_id)
        assert isinstance(self._id, int), reg_name
        self.sub = self.node.make_subscriber(self.data_type, self._id).receive_in_background(self._callback)

    def get_id_string(self):
        if not self.id_updated:
            string =  str(self._id)
        else:
            toggle = bool(int(time.time() * 1000) % 1000 > 500)
            string =  f"{Colors.OKCYAN}{self._id}{Colors.ENDC}" if toggle else str(self._id)
        return string

    def rate(self):
        return self._rate_estiamtor.get_rate()

    async def _callback(self, data, transfer_from : pycyphal.transport._transfer.TransferFrom):
        assert isinstance(transfer_from, pycyphal.transport._transfer.TransferFrom)
        self.data = data
        self._rate_estiamtor.register_message()

        if self.min is not None:
            self._save_min_max(self.data, self.min, self.max)
        else:
            self.min = copy.deepcopy(self.data)
            self.max = copy.deepcopy(self.data)

    def _save_min_max(self, data, min_msg, max_msg):
        public_attributes = [attr for attr in dir(data) if not attr.startswith('_') and attr.islower()]
        for attribute in public_attributes:
            value = getattr(data, attribute)
            type_name = str(type(value))[8:-2]
            if isinstance(value, int) or isinstance(value, float):
                setattr(min_msg, attribute, min(value, getattr(min_msg, attribute)))
                setattr(max_msg, attribute, max(value, getattr(max_msg, attribute)))
            elif any(type_name.startswith(prefix) for prefix in ['uavcan.', 'ds015.', 'reg.', 'zubax.']):
                self._save_min_max(value, getattr(min_msg, attribute), getattr(max_msg, attribute))
