#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import time
import asyncio
import copy
import logging
from typing import Any, Union
import pycyphal.application
from raccoonlab_tools.common.colorizer import Colors
from raccoonlab_tools.cyphal.utils import PortRegisterInterface

class Port:
    def __init__(self, node) -> None:
        self.id = None
        self.updated = False
        self.interface = PortRegisterInterface(node)

    async def retrieve_or_assign(self, node_id: int, reg_names: tuple, def_id: int):
        for reg_name in reg_names:
            await self._retrieve(node_id, reg_name)
            logging.debug(f"y r {node_id} {reg_name} # {self.id}")
            if self.id is not None:
                break
        if self.id is None:
            logging.warn(f"{reg_names} is not exist")
            return

        self.updated = not self._is_valid()

        if self.updated:
            await self._assign(node_id, reg_name, def_id)

        return self.id

    def _is_valid(self):
        return (self.id > 0) and (self.id < 8191)

    async def _retrieve(self, node_id: int, reg_name: str):
        self.id = await self.interface.get_id(node_id, reg_name)

    async def _assign(self, node_id: int, reg_name: str, port_id: int):
        self.id = await self.interface.set_id(node_id, reg_name, port_id)

    def __str__(self) -> str:
        if self.id is None:
            string =  f"{Colors.FAIL}None{Colors.ENDC}"
        elif not self.updated:
            string = str(self.id)
        else:
            toggle = bool(int(time.time() * 1000) % 1000 > 500)
            string =  f"{Colors.OKCYAN}{self.id}{Colors.ENDC}" if toggle else str(self.id)
        return string

class Topic:
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int,
                 def_id: int,
                 reg_name: str,
                 data_type: Any) -> None:
        assert isinstance(node, pycyphal.application._node_factory.SimpleNode)
        assert isinstance(node_id, int) and node_id >= 0 and node_id <= 65535
        assert isinstance(def_id, int) and def_id >= 0 and def_id <= 65535
        assert isinstance(reg_name, str) or isinstance(reg_name, tuple)
        self.node = node
        self.node_id = node_id
        self.def_id = def_id
        self.reg_names = reg_name if isinstance(reg_name, tuple) else (reg_name, )
        self.data_type = data_type
        self.msg = None

        self.port = Port(self.node)

    def __str__(self) -> str:
        return f"- {self.reg_names} {self.port.id} {self.msg}"

class Publisher(Topic):
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int,
                 def_id: int,
                 reg_name: str,
                 data_type: Any,
                 rate: Union[float, int]) -> None:
        super().__init__(node, node_id, def_id, reg_name, data_type)
        self.msg = self.data_type()
        self.period = 1.0 if rate < 0.01 else 1.0 / rate

    async def start_publishing(self) -> None:
        """
        Start an asynchronous task that continuously publishes self.msg with given rate
        """
        port_id = await self.port.retrieve_or_assign(self.node_id, self.reg_names, self.def_id)
        if port_id is None:
            return

        pub = self.node.make_publisher(self.data_type, port_id)

        async def start() -> None:
            while True:
                await pub.publish(self.msg)
                await asyncio.sleep(self.period)

        asyncio.create_task(start())

    def __str__(self) -> str:
        return super().__str__()

class RateEstimator:
    def __init__(self, window_size_sec=1.0) -> None:
        self._timestamps = []
        self._window_size_sec = window_size_sec

    def register_message(self):
        deadline = time.time() - self._window_size_sec
        self._timestamps = [timestamp for timestamp in self._timestamps if timestamp > deadline]
        self._timestamps.append(time.time())

    def get_rate(self) -> int:
        deadline = time.time() - self._window_size_sec
        self._timestamps = [timestamp for timestamp in self._timestamps if timestamp > deadline]
        return int(len(self._timestamps) / self._window_size_sec)

class Subscriber(Topic):
    def __init__(self,
                 node: pycyphal.application._node_factory.SimpleNode,
                 node_id: int,
                 def_id: int,
                 reg_name: str,
                 data_type) -> None:

        super().__init__(node, node_id, def_id, reg_name, data_type)
        self._rate_estimator = RateEstimator(window_size_sec=2.0)
        self.min = None
        self.max = None

    async def init(self):
        port_id = await self.port.retrieve_or_assign(self.node_id, self.reg_names, self.def_id)
        if port_id is None:
            return

        self.sub = self.node.make_subscriber(self.data_type, port_id)
        self.sub.receive_in_background(self._callback)

    def rate(self):
        return self._rate_estimator.get_rate()

    async def _callback(self, data, transfer_from : pycyphal.transport._transfer.TransferFrom):
        assert isinstance(transfer_from, pycyphal.transport._transfer.TransferFrom)
        self.msg = data
        self._rate_estimator.register_message()

        if self.min is not None:
            self._save_min_max(self.msg, self.min, self.max)
        else:
            self.min = copy.deepcopy(self.msg)
            self.max = copy.deepcopy(self.msg)

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
