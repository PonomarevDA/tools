#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
import os
import sys
import secrets
import subprocess
import pytest
import dronecan
import time
import random
from enum import IntEnum

from raccoonlab_tools.common.protocol_parser import CanProtocolParser, Protocol
from raccoonlab_tools.dronecan.global_node import DronecanNode
from raccoonlab_tools.dronecan.utils import Parameter, ParametersInterface, NodeCommander

PARAM_UAVCAN_NODE_ID                = "uavcan.node.id" 
PARAM_BATTERY_SOC_PCT               = "battery.soc_pct"
PARAM_BATTERY_ID                    = "battery.battery_id"
PARAM_BATTERY_MODEL_INSTANCE_ID     = "battery.model_instance_id"
PARAM_BATTERY_CAPACITY_MAH          = "battery.capacity_mah"
PARAM_BATTERY_FULL_VOLTAGE_MV       = "battery.full_voltage_mv"
PARAM_BATTERY_EMPTY_VOLTAGE_MV      = "battery.empty_voltage_mv"
PARAM_BUZZER_ERROR_MELODY           = "buzzer.error_melody"
PARAM_BUZZER_ARM_MELODY             = "buzzer.arm_melody"
PARAM_BUZZER_FREQUENCY              = "buzzer.frequency"
PARAM_BUZZER_BEEP_FRACTION          = "buzzer.beep_fraction"
PARAM_BUZZER_BEEP_PERIOD            = "buzzer.beep_period"
PARAM_BUZZER_VERBOSE                = "buzzer.verbose"
PARAM_GATE_THRESHOLD                = "gate.threshold"

class ErrorMelodies(IntEnum):
    ANNOYING = 0
    TOLERABLE = 1
    BIMMER = 2
    DEFINED_BY_PARAMS = 127

class ParamLightsType(IntEnum):
    SOLID = 0
    BLINKING = 1
    PULSING = 2

class PMUNode:
    
    min_frequency: int = 50

    def __init__(self) -> None:
        self.node = DronecanNode()

    def send_beeper_command(self, msg:dronecan.uavcan.equipment.indication.BeepCommand) -> None:
        self.node.publish(msg)

    def recv_sound(self, timeout_sec=0.03):
        res = self.node.sub_once(dronecan.uavcan.equipment.indication.BeepCommand, timeout_sec)
        return res.message
    
    def configure(self, config):
        params = ParametersInterface()
        commander = NodeCommander()

        params.set(config)
        commander.store_persistent_states()
        commander.restart()

def make_beeper_cmd_from_values(frequency: float, duration:float):
    return dronecan.uavcan.equipment.indication.BeepCommand(frequency=frequency, duration=duration)

def compare_beeper_command_values(first: dronecan.uavcan.equipment.indication.BeepCommand, second: dronecan.uavcan.equipment.indication.BeepCommand):
    return first.duration == second.duration and first.frequency == second.frequency

def compare_beeper_command_duration_values(first: dronecan.uavcan.equipment.indication.BeepCommand, expected_duration: float):
    return first.duration == expected_duration

# 1
@pytest.mark.dependency()
def test_transport():
    """
    This test is required just for optimization purposes.
    Let's skip all tests if we don't have an online Cyphal node.
    """
    assert CanProtocolParser.verify_protocol(white_list=[Protocol.DRONECAN])

# 2
@pytest.mark.dependency()
def test_beeper_command_feedback():
    pmu = PMUNode()
    config = [Parameter(name=PARAM_BUZZER_VERBOSE, value=1)]
    pmu.configure(config)
    time.sleep(5)
    recv_sound = pmu.recv_sound()
    assert recv_sound is not None

@pytest.mark.dependency(depends=["test_transport", "test_beeper_command_feedback"])
class TestGateOk:
    threshold = 0
    config = [
        Parameter(name=PARAM_BATTERY_ID, value=0),
        Parameter(name=PARAM_BATTERY_MODEL_INSTANCE_ID, value=0),
        Parameter(name=PARAM_BUZZER_ERROR_MELODY, value=127),
        Parameter(name=PARAM_BUZZER_FREQUENCY, value=ParamLightsType.SOLID),
        Parameter(name=PARAM_GATE_THRESHOLD, value=0),
        # Parameter(name=PARAM_GATE_THRESHOLD, value=4095),
        Parameter(name=PARAM_BUZZER_VERBOSE, value=1),
    ]
    pmu = PMUNode()

    @staticmethod
    def configure_node():
        TestGateOk.pmu.configure(TestGateOk.config)
        time.sleep(5)

    # 3
    @staticmethod
    def test_healthy_node_sound_after_restart():
        pmu = TestGateOk.pmu
        TestGateOk.configure_node()
        recv = pmu.recv_sound()
        expected_duration = 0

        assert compare_beeper_command_duration_values(recv, expected_duration=expected_duration)
    
    # 4
    @pytest.mark.dependency(depends=["test_healthy_node_sound_after_restart"])
    @staticmethod
    def test_send_random_sound():
        pmu = TestGateOk.pmu

        frequency = random.randrange(PMUNode.min_frequency, 1000)
        duration = 2
        cmd = make_beeper_cmd_from_values(frequency=frequency, duration=duration)
        pmu.send_beeper_command(cmd)
        sound = None

        for i in range(20):
            sound = pmu.recv_sound()
            if sound is not None and compare_beeper_command_values(sound, cmd):
                break
        assert compare_beeper_command_values(sound, cmd)

    # 5
    @pytest.mark.dependency(depends=["test_send_random_sound"])
    @staticmethod
    def test_silence_after_command_ttl():
        pmu = TestGateOk.pmu

        frequency = random.randrange(PMUNode.min_frequency, 1000)
        duration = random.uniform(0.1, 1)

        msg = make_beeper_cmd_from_values(frequency=frequency, duration=duration)
        pmu.send_beeper_command(msg)

        time.sleep(duration)

        for _ in range(20):
            recv = pmu.recv_sound()
        assert compare_beeper_command_duration_values(recv, expected_duration=0)

    # 6
    @staticmethod
    def test_beep_command_subscription():
        pmu = TestGateOk.pmu

        expected_counter = 0
        unexpected_counter = 0

        number_of_notes = 20
        for i in range(number_of_notes):
            frequency = random.randrange(PMUNode.min_frequency, 1000)
            duration = random.uniform(0.1, 1)
            msg = make_beeper_cmd_from_values(frequency=frequency, duration=duration)
            pmu.send_beeper_command(msg)
            start_time = time.time()
            timeout_sec = 0.05
            while (time.time() - start_time < duration - timeout_sec):
                for _ in range(15):
                    recv = pmu.recv_sound()
                    if recv is not None:
                        break
                if compare_beeper_command_values(recv, msg):
                    expected_counter += 1
                else:
                    unexpected_counter += 1

        total_counter = expected_counter + unexpected_counter

        hint = (
            f"{TestGateOk.__doc__}. "
            f"Expected: {expected_counter}/{total_counter}. "
            f"Unexpected: {unexpected_counter}/{total_counter}. "
        )

        assert unexpected_counter == 0, f"{hint}"
        assert expected_counter > 0, f"{hint}"

    # 7
    @staticmethod
    def test_beep_command_subscription_with_duration():
        pmu = TestGateOk.pmu

        expected_counter = 0
        unexpected_counter = 0

        duration_comply_failure_counter = 0
        number_of_notes = 20
        for i in range(number_of_notes):
            frequency = random.randrange(PMUNode.min_frequency, 1000)
            duration = random.uniform(0.1, 1)
            msg = make_beeper_cmd_from_values(frequency=frequency, duration=duration)
            pmu.send_beeper_command(msg)
            start_time = time.time()
            timeout_sec = 0.05
            while (time.time() - start_time < duration - timeout_sec):
                for _ in range(15):
                    recv = pmu.recv_sound()
                    if recv is not None:
                        break
                if compare_beeper_command_values(recv, msg):
                    expected_counter += 1
                else:
                    unexpected_counter += 1

            for _ in range(15):
                recv = pmu.recv_sound()

            if not compare_beeper_command_duration_values(recv, expected_duration=0):
                duration_comply_failure_counter += 1

        total_counter = expected_counter + unexpected_counter

        hint = (
            f"{TestGateOk.__doc__}. "
            f"Expected: {expected_counter}/{total_counter}. "
            f"Unexpected: {unexpected_counter}/{total_counter}. "
            f"Duration comply failures: {duration_comply_failure_counter}/{number_of_notes}. "
        )

        assert unexpected_counter == 0, f"{hint}"
        assert expected_counter > 0, f"{hint}"
        assert duration_comply_failure_counter == 0, f"{hint}"

def main():
    cmd = ["pytest", os.path.abspath(__file__)]
    cmd += ['--tb=no']  # No traceback at all
    cmd += ['-v']  # Increase verbosity
    cmd += ['-W', 'ignore::DeprecationWarning']  # Ignore specific warnings
    cmd += sys.argv[1:] # Forward optional user flags
    print(len(cmd))
    print(cmd)
    sys.exit(subprocess.call(cmd))

if __name__ == "__main__":
    main()
