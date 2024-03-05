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
from enum import IntEnum

from raccoonlab_tools.common.protocol_parser import CanProtocolParser, Protocol
from raccoonlab_tools.dronecan.global_node import DronecanNode
from raccoonlab_tools.dronecan.utils import Parameter, ParametersInterface, NodeCommander

PARAM_LIGHTS_ID                 = 'lights.id'
PARAM_LIGHTS_MAX_INTENSITY      = 'lights.max_intensity'
PARAM_LIGHTS_DEFAULT_COLOR      = 'lights.default_color'
PARAM_LIGHTS_TYPE               = 'lights.type'
PARAM_LIGHTS_BLINK_PERIOD       = 'lights.blink_period_ms'
PARAM_LIGHTS_DUTY_CYCLE_PCT     = 'lights.duty_cycle_pct'
PARAM_LIGHTS_VERBOSE            = 'lights.verbose'

class ParamLightsId(IntEnum):
    UI_LEDS = 0

class Colors(IntEnum):
    RED = 0
    GREEN = 1
    BLUE = 2
    MAGNETA = 3
    YELLOW = 4
    CYAN = 5
    WHITE = 6

class ParamLightsType(IntEnum):
    SOLID = 0
    BLINKING = 1
    PULSING = 2


RGB565_FROM_COLOR = [
    dronecan.uavcan.equipment.indication.RGB565(red=31, green=0, blue=0),
    dronecan.uavcan.equipment.indication.RGB565(red=0, green=63, blue=0),
    dronecan.uavcan.equipment.indication.RGB565(red=0, green=0, blue=31),
    dronecan.uavcan.equipment.indication.RGB565(red=31, green=0, blue=31),
    dronecan.uavcan.equipment.indication.RGB565(red=31, green=63, blue=0),
    dronecan.uavcan.equipment.indication.RGB565(red=0, green=63, blue=31),
    dronecan.uavcan.equipment.indication.RGB565(red=31, green=63, blue=31),
]


class LightsNode:
    def __init__(self) -> None:
        self.node = DronecanNode()

    def send_single_light_command(self, red: int, green: int, blue: int, id: int = 0) -> None:
        msg = dronecan.uavcan.equipment.indication.LightsCommand(commands=[
            dronecan.uavcan.equipment.indication.SingleLightCommand(
                light_id=id,
                color=dronecan.uavcan.equipment.indication.RGB565(
                    red=red,
                    green=green,
                    blue=blue
        ))])
        self.node.publish(msg)

    def recv_color(self, timeout_sec=0.03):
        res = self.node.sub_once(dronecan.uavcan.equipment.indication.LightsCommand, timeout_sec)
        color = res.message.commands[0].color
        return color

    def send_raw_command(self, cmd : list) -> None:
        msg = dronecan.uavcan.equipment.esc.RawCommand(cmd=cmd)
        self.node.publish(msg)

    def configure(self, config):
        params = ParametersInterface()
        commander = NodeCommander()

        params.set(config)
        commander.store_persistent_states()
        commander.restart()

def compare_colors(first: dronecan.uavcan.equipment.indication.LightsCommand,
                   second: dronecan.uavcan.equipment.indication.LightsCommand) -> bool:
    return first.red == second.red and first.green == second.green and first.blue == second.blue


@pytest.mark.dependency()
def test_transport():
    """
    This test is required just for optimization purposes.
    Let's skip all tests if we don't have an online Cyphal node.
    """
    assert CanProtocolParser.verify_protocol(white_list=[Protocol.DRONECAN])

@pytest.mark.dependency()
def test_lights_feedback():
    lights = LightsNode()
    config = [Parameter(name=PARAM_LIGHTS_VERBOSE, value=1)]
    lights.configure(config)
    recv_color = lights.recv_color()
    assert recv_color is not None


@pytest.mark.dependency(depends=["test_transport", "test_lights_feedback"])
class TestSolid:
    """Solid mode and (arm or no LightsCommand) => color must be constant"""
    color = secrets.choice(list(Colors))
    random_color_config = [
        Parameter(name=PARAM_LIGHTS_ID, value=ParamLightsId.UI_LEDS),
        Parameter(name=PARAM_LIGHTS_MAX_INTENSITY, value=100),
        Parameter(name=PARAM_LIGHTS_DEFAULT_COLOR, value=color),
        Parameter(name=PARAM_LIGHTS_TYPE, value=ParamLightsType.SOLID),
        Parameter(name=PARAM_LIGHTS_BLINK_PERIOD, value=secrets.randbelow(1001)),
        Parameter(name=PARAM_LIGHTS_DUTY_CYCLE_PCT, value=secrets.randbelow(101)),
        Parameter(name=PARAM_LIGHTS_VERBOSE, value=1),
    ]

    @staticmethod
    def test_random_color_after_restart():
        """
        After the initialization, the node must have the configured color.
        """
        lights = LightsNode()
        lights.configure(TestSolid.random_color_config)

        recv = lights.recv_color()
        expected = RGB565_FROM_COLOR[TestSolid.color]

        assert compare_colors(recv, expected), (f"{TestSolid.color}: {recv} != {expected}")

    @staticmethod
    @pytest.mark.skip(reason="not implemented yet")
    def test_random_color_when_armed():
        pass  # add implementation here


@pytest.mark.dependency(depends=["test_transport", "test_lights_feedback"])
class TestBlinking:
    """Blink mode and (arm or no LightsCommand) => color must blink"""
    color = secrets.choice(list(Colors))
    config = [
            Parameter(name=PARAM_LIGHTS_ID, value=ParamLightsId.UI_LEDS),
            Parameter(name=PARAM_LIGHTS_MAX_INTENSITY, value=100),
            Parameter(name=PARAM_LIGHTS_DEFAULT_COLOR, value=color),
            Parameter(name=PARAM_LIGHTS_TYPE, value=ParamLightsType.BLINKING),
            Parameter(name=PARAM_LIGHTS_BLINK_PERIOD, value=1000),
            Parameter(name=PARAM_LIGHTS_DUTY_CYCLE_PCT, value=secrets.randbelow(81) + 10),
            Parameter(name=PARAM_LIGHTS_VERBOSE, value=1),
        ]
    @staticmethod
    def test_after_restart():
        lights = LightsNode()
        lights.configure(TestBlinking.config)

        enabled_color = RGB565_FROM_COLOR[TestBlinking.color]
        disabled_color = dronecan.uavcan.equipment.indication.RGB565(red=0, green=0, blue=0)

        enabled_counter = 0
        disabled_counter = 0
        unexpected_counter = 0

        # Skip first enabled wave
        for _ in range(100):
            color = lights.recv_color()
            if compare_colors(color, enabled_color):
                enabled_counter += 1
            elif compare_colors(color, disabled_color):
                disabled_counter += 1
            else:
                unexpected_counter += 1

        total_counter = enabled_counter + disabled_counter + unexpected_counter

        hint = (
            f"{TestBlinking.__doc__}. "
            f"Enabled: {enabled_counter}/{total_counter}. "
            f"Disabled: {disabled_counter}/{total_counter}. "
            f"Unexpected: {unexpected_counter}/{total_counter}. "
        )

        assert unexpected_counter == 0, f"{hint}"
        assert enabled_counter > 0, f"{hint}"
        assert disabled_counter > 0, f"{hint}"


@pytest.mark.dependency(depends=["test_transport", "test_lights_feedback"])
class TestUiLedsMode:
    """UI RGB LEDs mode"""
    color = secrets.choice(list(Colors))
    random_config = [
        Parameter(name=PARAM_LIGHTS_ID, value=ParamLightsId.UI_LEDS),
        Parameter(name=PARAM_LIGHTS_MAX_INTENSITY, value=100),
        Parameter(name=PARAM_LIGHTS_DEFAULT_COLOR, value=color),
        Parameter(name=PARAM_LIGHTS_TYPE, value=secrets.randbelow(3)),
        Parameter(name=PARAM_LIGHTS_BLINK_PERIOD, value=secrets.randbelow(1001)),
        Parameter(name=PARAM_LIGHTS_DUTY_CYCLE_PCT, value=secrets.randbelow(101)),
        Parameter(name=PARAM_LIGHTS_VERBOSE, value=1),
    ]
    @staticmethod
    def test_ui_leds_mode(length=128):
        """Disarmed => the light is controlled by the LightCommand command"""
        lights = LightsNode()
        lights.configure(TestUiLedsMode.random_config)

        recv_colors = []
        for idx in range(length):
            lights.send_single_light_command(red=idx%32, green=idx%64, blue=idx%32, id=ParamLightsId.UI_LEDS)
            lights.node.node.spin(0.05)
            for _ in range(10):
                color = lights.recv_color()
            recv_colors.append(color)

        for idx, color in enumerate(recv_colors):
            expected = dronecan.uavcan.equipment.indication.RGB565(red=idx%32, green=idx%64, blue=idx%32)
            assert compare_colors(color, expected), f"{TestUiLedsMode.__doc__}: {color} != {expected}"


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
