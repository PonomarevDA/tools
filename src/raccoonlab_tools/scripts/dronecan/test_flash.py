#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Anastasiia Stepanova.
# Author: Anastasiia Stepanova <asiiapine@gmail.com>

import os
import string
import sys
import secrets
import subprocess
from typing import List
import pytest
import dronecan

from raccoonlab_tools.common.protocol_parser import CanProtocolParser, Protocol
from raccoonlab_tools.dronecan.global_node import DronecanNode
from raccoonlab_tools.dronecan.utils import (
    Parameter,
    ParametersInterface,
    NodeCommander,
)

PARAM_NODE_ID = "uavcan.node.id"
PARAM_SYSTEM_NAME = "system.name"

def generate_random_str():
    return ''.join([secrets.choice(string.ascii_uppercase +
                    string.digits) for i in range(56)])

class Node:
    def __init__(self) -> None:
        self.node = DronecanNode()
        assert isinstance(self.node.node, dronecan.node.Node)
        self.params_interface = ParametersInterface()
        self.commander = NodeCommander()
        
        self.params : List[Parameter]       = []
        self.int_params : List[Parameter]   = []
        self.str_params : List[Parameter]   = []
        self.__get_parameters__()

    def recv_parameter_value(self, idx_or_name: int | str) -> int|str:
        res = self.params_interface.get(idx_or_name)
        return res.value

    def set_random_str_param(self, param_or_name: str | Parameter) -> str:
        """
        The function sets random string value to random node's parameter of type string
        @returns: name of the modified parameter and the sting value
        """
        param_name = param_or_name
        if isinstance(param_or_name, Parameter):
            assert param_or_name.min_value is None
            param_name = param_or_name.name
        value = generate_random_str()
        self.params_interface.set(Parameter(name=param_name, value=value))
        return value

    def set_random_int_param(self, param: Parameter) -> int:
        """
        The function sets random int value to node's parameter of type integer
        @returns: name of the modified parameter and the int value
        """
        assert param.min_value is not None
        value = param.min_value + secrets.randbelow(param.max_value - param.min_value)
        self.params_interface.set(Parameter(name=param.name, value=value))
        return value

    def __get_parameters__(self) -> None:
        params: List[Parameter] = self.params_interface.get_all()
        for param in params:
            if param.name == PARAM_NODE_ID or param.name == PARAM_SYSTEM_NAME:
                continue
            if isinstance(param.value, int):
                self.int_params.append(param)
            elif isinstance(param.value, str):
                self.str_params.append(param)
        self.params = params

@pytest.mark.tryfirst
@pytest.mark.dependency()
def test_transport():
    """
    This test is required just for optimization purposes.
    Let's skip all tests if we don't have an online Dronecan node.
    """
    assert CanProtocolParser.verify_protocol(white_list=[Protocol.DRONECAN])

@pytest.mark.dependency()
def test_feedback():
    node = Node()
    res = node.recv_parameter_value(PARAM_NODE_ID)
    assert res is not None

@pytest.mark.dependency(depends=["test_feedback"])
class TestGetSet:
    node = Node()

    @staticmethod
    def test_set_get_str():
        node = TestGetSet.node
        if not node.str_params:
            return
        param = secrets.choice(node.str_params[1:])
        value = node.set_random_str_param(param.name)
        res = str(node.recv_parameter_value(param.name)).replace("\x01", '')
        assert res == value

    @staticmethod
    def test_set_get_int():
        node = TestGetSet.node
        if not node.int_params:
            return
        param = secrets.choice(node.int_params[1:])
        value = node.set_random_int_param(param)
        res = node.recv_parameter_value(param.name)
        assert res == value

@pytest.mark.dependency(depends=["TestGetSet"])
class TestGetSetVsRestart:
    node = Node()

    @pytest.mark.dependency(depends=["TestGetSet::test_set_get_int"])
    @staticmethod
    def test_restart_int_delayed():
        node = TestGetSetVsRestart.node
        if not node.int_params:
            return
        param = secrets.choice(node.int_params[1:])
        init_val = node.recv_parameter_value(param.name)
        value = node.set_random_int_param(param)

        node.commander.store_persistent_states()
        node.node.node.spin(1)

        node.commander.restart()
        res = node.recv_parameter_value(param.name)
        hint = (
            f"{TestGetSetVsRestart.__doc__}. "
            f"Expected: {value}. "
            f"Received: {res}. "
            f"Init value: {init_val}. "
        )

        assert res == value, f"{hint}"

    @pytest.mark.dependency(depends=["TestGetSetVsRestart::test_restart_int_delayed"])
    @staticmethod
    def test_restart_num():
        node = TestGetSetVsRestart.node
        if not node.int_params:
            return
        new_value_stated = 0
        old_value_remained = 0
        value_set_before_restart = 0
        for i in range(20):
            param = secrets.choice(node.int_params[1:])
            init_value = node.recv_parameter_value(param.name)
            value = init_value
            while value == init_value:
                value = node.set_random_int_param(param)

            node.commander.store_persistent_states()

            res_before_restart = node.recv_parameter_value(param.name)
            if res_before_restart == value:
                value_set_before_restart += 1
            node.commander.restart()
            res = node.recv_parameter_value(param.name)
            if res == value:
                new_value_stated += 1
            elif res == init_value:
                old_value_remained += 1

        total_counter = old_value_remained + new_value_stated

        hint = (
            f"{TestGetSetVsRestart.__doc__}. "
            f"New value stated: {new_value_stated}/{total_counter}. "
            f"Old value remained: {old_value_remained}/{total_counter}. "
            f"Value changed before restart: {value_set_before_restart}/{total_counter}. "
        )

        assert old_value_remained == 0, f"{hint}"
        assert new_value_stated > 0, f"{hint}"

    @pytest.mark.dependency(depends=["TestGetSet::test_set_get_str"])
    @staticmethod
    def test_restart_str_delayed():
        node = TestGetSetVsRestart.node
        if not node.str_params:
            return
        param = secrets.choice(node.str_params[1:])
        value = node.set_random_str_param(param.name)
        node.commander.store_persistent_states()
        node.commander.restart()
        node.node.node.spin(1)

        res = str(node.recv_parameter_value(param.name)).replace("\x01", "")
        assert res == value

    @pytest.mark.dependency(depends=["TestGetSetVsRestart::test_restart_str_delayed"])
    @staticmethod
    def test_restart_str():
        node = TestGetSetVsRestart.node
        if not node.str_params:
            return
        new_value_stated = 0
        old_value_remained = 0
        value_set_before_restart = 0
            
        for i in range(20):
            try:
                param = secrets.choice(node.str_params[1:])
                init_value = str(node.recv_parameter_value(param.name)).replace("\x01", "")
                value = init_value
                while value == init_value:
                    value = str(node.recv_parameter_value(param.name)).replace("\x01", "")

                node.commander.store_persistent_states()

                res_before_restart = str(node.recv_parameter_value(param.name)).replace("\x01", "")
                if res_before_restart == value:
                    value_set_before_restart += 1
                node.commander.restart()
                res = str(node.recv_parameter_value(param.name)).replace("\x01", "")
                if res == value:
                    new_value_stated += 1
                elif res == init_value:
                    old_value_remained += 1
            except Exception as e:
                print(e)
                continue
        total_counter = old_value_remained + new_value_stated

        hint = (
            f"{TestGetSetVsRestart.__doc__}. "
            f"New value stated: {new_value_stated}/{total_counter}. "
            f"Old value remained: {old_value_remained}/{total_counter}. "
            f"Value changed before restart: {value_set_before_restart}/{total_counter}. "
        )

        assert old_value_remained == 0, f"{hint}"
        assert new_value_stated > 0, f"{hint}"



def main():
    cmd = ["pytest", os.path.abspath(__file__)]
    cmd += ["--tb=no"]  # No traceback at all
    cmd += ["-v"]  # Increase verbosity
    cmd += ["-W", "ignore::DeprecationWarning"]  # Ignore specific warnings
    cmd += sys.argv[1:]  # Forward optional user flags
    print(len(cmd))
    print(cmd)
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
