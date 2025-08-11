#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Anastasiia Stepanova.
# Author: Anastasiia Stepanova <asiiapine@gmail.com>

import os
import time
import sys
import string
import secrets
import subprocess
from typing import List
from enum import Enum
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

ENG_TIME_PARAM_NAME = "stats.engaged_time"
LOG_LEVEL_PARAM_NAME = "system.log_level"

ICE_THR_CHANNEL = 7
raw_command_array_disarmed  = [0]*(ICE_THR_CHANNEL + 1)
raw_command_array_armed     = [0]*(ICE_THR_CHANNEL + 1)
raw_command_array_armed[ICE_THR_CHANNEL] = 1


class ArmingCommand:
    def __init__(self, arm, disarm):
        self.arm = arm
        self.disarm = disarm

mode_command: ArmingCommand = ArmingCommand(
                                    arm=dronecan.uavcan.equipment.safety.ArmingStatus(status=255),
                                    disarm=dronecan.uavcan.equipment.safety.ArmingStatus(status=0))
raw_command: ArmingCommand = ArmingCommand(
                    arm=dronecan.uavcan.equipment.esc.RawCommand(cmd=raw_command_array_armed),
                    disarm=dronecan.uavcan.equipment.esc.RawCommand(cmd=raw_command_array_disarmed))


class ARM_CMD_OPTINS(Enum):
    MODE_VERSION = mode_command
    RAW_COMMAND_VERSION = raw_command


class Node:
    def __init__(self, arming_command: ARM_CMD_OPTINS = ARM_CMD_OPTINS.RAW_COMMAND_VERSION) -> None:
        self.node = DronecanNode()
        assert isinstance(self.node.node, dronecan.node.Node)
        self.params_interface = ParametersInterface()
        self.node_id = self.params_interface._target_node_id
        self.commander = NodeCommander()
        self.params : List[Parameter]       = []
        self.int_params : List[Parameter]   = []
        self.str_params : List[Parameter]   = []
        self.engaged_time_param_idx = None
        self.log_level_param_idx = None
        self.arming_command = arming_command.value
        self.__get_parameters__()

    def recv_parameter_value(self, idx_or_name: int | str) -> int|str:
        res = self.params_interface.get(idx_or_name)
        return res.value

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
        self.find_engaged_time_param()
        self.find_log_level_param()

    def find_engaged_time_param(self) -> int:
        for idx, param in enumerate(self.int_params):
            if param.name == ENG_TIME_PARAM_NAME:
                self.engaged_time_param_idx = idx
                return idx
        for idx, param in enumerate(self.str_params):
            if param.name == ENG_TIME_PARAM_NAME:
                raise Exception(f"Parameter {ENG_TIME_PARAM_NAME} is not an integer")
        raise Exception(f"Parameter {ENG_TIME_PARAM_NAME} not found")

    def find_log_level_param(self) -> int:
        for idx, param in enumerate(self.int_params):
            if param.name == LOG_LEVEL_PARAM_NAME:
                self.log_level_param_idx = idx
                return idx
        for idx, param in enumerate(self.str_params):
            if param.name == LOG_LEVEL_PARAM_NAME:
                raise Exception(f"Parameter {LOG_LEVEL_PARAM_NAME} is not an integer")
        raise Exception(f"Parameter {LOG_LEVEL_PARAM_NAME} not found")

    def send_arming_command(self):
        self.node.node.broadcast(self.arming_command.arm)
    
    def send_disarming_command(self):
        self.node.node.broadcast(self.arming_command.disarm)

    def send_log_level(self, level: int):
        self.params_interface.set(Parameter(name=LOG_LEVEL_PARAM_NAME, value=level))
        self.commander.store_persistent_states()
        self.commander.restart()

    def get_eng_time(self):
        return self.params_interface.get(ENG_TIME_PARAM_NAME).value


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
    print(node.params)
    res = node.recv_parameter_value(PARAM_NODE_ID)
    assert res is not None

@pytest.mark.dependency(depends=["test_feedback"])
class TestGetSet:
    node = Node()

    @staticmethod
    def test_set_get_eng_time():
        node = TestGetSet.node
        if not node.int_params:
            return
        param = node.int_params[node.engaged_time_param_idx]
        value = node.set_random_int_param(param)
        res = node.recv_parameter_value(param.name)
        assert res == value
    

@pytest.mark.dependency(depends=["TestGetSet::test_set_get_eng_time"])
class TestLogsModeArming:
    node = Node()
    log_message: None | str = None
    engaged_time: None | int = None

    @staticmethod
    def handle_log_message(msg: dronecan.uavcan.protocol.debug.LogMessage):
        if msg.transfer.source_node_id != TestLogsModeArming.node.node_id:
            return
        if not str(msg.message.text).startswith("Engaged time"):
            return
        TestLogsModeArming.log_message = str(msg.message.text)

    @staticmethod
    def test_log_level():
        node = TestLogsModeArming.node
        if not node.int_params:
            return
        param = node.int_params[node.log_level_param_idx]
        value = node.set_random_int_param(param)
        node.send_log_level(value)
        res = node.recv_parameter_value(param.name)
        assert res == value

    @staticmethod
    def test_engaged_time_update():
        node = TestLogsModeArming.node
        init_eng_time = node.get_eng_time()

        # Send log level 0 to enable all logs
        node.send_log_level(0)
        # Add handler to receive log messages
        node.node.node.add_handler(dronecan.uavcan.protocol.debug.LogMessage,
                                    TestLogsModeArming.handle_log_message)

        expected_time_diff_s = 10
        start_time = time.time()
        # send arming command expected_time_diff_s seconds
        while time.time() - start_time < expected_time_diff_s:
            node.send_arming_command()
            node.node.node.spin(0.2)

        waiting_time = 3
        waiting_start_time = time.time()
        # Wait for waiting_time until the node updates mode and sends log message
        while TestLogsModeArming.log_message is None and \
                time.time() - waiting_start_time < waiting_time:
            node.node.node.spin(0.2)

        # Check that the node sends log message
        if TestLogsModeArming.log_message is None:
            raise Exception("Log message not received")

        # Receive updated engaged time parameter
        new_eng_time = node.get_eng_time()

        assert new_eng_time > init_eng_time
        assert abs((new_eng_time - init_eng_time) - expected_time_diff_s) < waiting_time
        TestLogsModeArming.engaged_time = new_eng_time

    @staticmethod
    def test_log_message():
        hours = int(TestLogsModeArming.engaged_time / 3600)
        minutes = int((TestLogsModeArming.engaged_time % 3600) / 60)
        assert TestLogsModeArming.log_message == f"Engaged time H: {hours} m: {minutes}"

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
