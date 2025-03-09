#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2025 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
"""
Simulated DroneCAN Internal Combustion Engine (ICE)
"""
import sys
import time
import math
import logging
import argparse
from typing import Optional

import numpy as np
import dronecan

logger = logging.getLogger(__name__)

class Controller:
    """
    +-----------------------------+     +-----------------------------+
    |          INPUTS             | --> |          OUTPUTS            |
    +-----------------------------+     +-----------------------------+
    | in_gas_throttle_pct         |     | out_gas_throttle_pct        |
    | in_gas_throttle_timestamp   |     | out_air_throttle_pct        |
    | in_air_throttle_pct         |     | out_starter_enabled         |
    | measured_rpm                |     | out_spark_ignition_enabled  |
    +-----------------------------+     +-----------------------------+
    """
    EXPECTED_MIN_RPM = 1500

    def __init__(self):
        # Input
        self.in_gas_throttle_pct = 0
        self.in_gas_throttle_timestamp = 0.0
        self.measured_rpm = 0.0

        if not hasattr(self, 'in_air_throttle_pct'):
            self.in_air_throttle_pct = 0
        if not hasattr(self, 'in_air_throttle_timestamp'):
            self.in_air_throttle_timestamp = 0

        # Internal
        self.state = 0
        self.start_time = 0

        # Output
        self.out_gas_throttle_pct = int(0)
        self.out_air_throttle_pct = int(0)
        self.out_starter_enabled = False
        self.out_spark_ignition_enabled = False

    def update_controller(self, measured_rpm: int):
        assert isinstance(measured_rpm, int)

        if self.in_gas_throttle_pct <= 0:
            self._reset()
            return

        crnt_time = time.time()

        self.out_spark_ignition_enabled = True
        self.out_gas_throttle_pct = self.in_gas_throttle_pct
        self.out_air_throttle_pct = self.in_air_throttle_pct

        if measured_rpm > self.EXPECTED_MIN_RPM:
            self.state = 2
            self.out_starter_enabled = False
        else:
            self.state = 1
            self.out_starter_enabled = int(crnt_time * 1000) % 4000 < 2000

    def set_gas_throttle_pct(self, in_gas_throttle_pct):
        self.in_gas_throttle_pct = max(0, min(in_gas_throttle_pct, 100))
        self.in_gas_throttle_timestamp = time.time()

    def get_voltage_5v(self) -> float:
        return 5.0

    def get_voltage_vin(self) -> float:
        return 50.0

    def get_internal_stm32_temperature_kelvin(self) -> float:
        return 273.15 + Engine.ENVIRONMENT_TEMPERATURE_CELSIUS

    def _reset(self):
        self.__init__()

    def __str__(self):
        return ("Controller("
                f"gas={self.in_gas_throttle_pct}%, "
                f"air={self.in_air_throttle_pct}%, "
                f"starter={self.out_starter_enabled}, "
                f"ignition={self.out_spark_ignition_enabled})")

class Engine:
    """
    +-----------------------------+     +-----------------------------+
    |          INPUTS             | --> |          OUTPUTS            |
    +-----------------------------+     +-----------------------------+
    | in_gas_throttle_pct         |     | rpm                         |
    | in_air_throttle_pct         |     | temperature                 |
    | in_starter_enabled          |     | voltage                     |
    | in_spark_ignition_enabled   |     | current                     |
    +-----------------------------+     +-----------------------------+
    """
    T1 = 0.5
    T2 = 30.0

    # When the engine’s cylinder head temperature (CHT) is below this temperature, the output is
    # poor. At these lower temperatures the fuel vaporization and combustion are not yet optimal.
    COLD_TRESHOLD_CELCIUS = 50

    # As temperatures creep upward, engine output tends to decline. The combustion process can
    # become less efficient and detonation risks may increase.
    HOT_TRESHOLD_CELCIUS = 170

    # When the CHT approaches this temperature or above, this is considered a red‑flag zone.
    # Sustained operation at these temperatures may lead to accelerated wear or even failure
    # (for example, piston or cylinder damage).
    CRITICAL_TRESHOLD_CELSIUS = 200

    # The simulator will target this temperature when working on 100% performance for a long time.
    ENVIRONMENT_TEMPERATURE_CELSIUS = 0
    MAX_SIMULATED_TEMPERATURE_CELSIUS = 250

    # The EME35 starter's loaded RPM typically falls between 700–1200 RPM
    STARTER_RPM = 800

    ICE_IDLE_RPM = 2500
    ICE_MAX_RPM = 9000

    def __init__(self):
        self.rpm = int(0)
        self.temperature_celsius = float(self.ENVIRONMENT_TEMPERATURE_CELSIUS)
        self.failure_deadline = 0.0

        self.in_gas_throttle_pct = 0
        self.in_air_throttle_pct = 0
        self.in_starter_enabled = False
        self.in_spark_ignition_enabled = False

        self._rng = np.random.default_rng()

    def get_noisy_rpm(self, sigma=300.0) -> int:
        assert isinstance(sigma, float)

        if self.rpm < 100:
            return int(0)

        noisy_rpm = self._rng.normal(loc=self.rpm, scale=sigma, size=1)[0]
        return int(max(0, noisy_rpm))

    def update_engine(self, gas_throttle_pct: int,
                            air_throttle_pct: int,
                            starter_enabled: bool,
                            spark_ignition_enabled: bool) -> None:
        assert isinstance(gas_throttle_pct, int)
        assert isinstance(air_throttle_pct, int)
        assert isinstance(starter_enabled, bool)
        assert isinstance(spark_ignition_enabled, bool)

        self.in_gas_throttle_pct = gas_throttle_pct
        self.in_air_throttle_pct = air_throttle_pct
        self.in_starter_enabled = starter_enabled
        self.in_spark_ignition_enabled = spark_ignition_enabled

        if self.in_starter_enabled:
            starter_target_rpm = self.STARTER_RPM
        else:
            starter_target_rpm = 0.0

        if self.rpm >= 100 and gas_throttle_pct >= 10 and spark_ignition_enabled and self.failure_deadline < time.time():
            engine_target_rpm = self.ICE_IDLE_RPM + (self.ICE_MAX_RPM - self.ICE_IDLE_RPM) * gas_throttle_pct / 100
            engine_target_rpm *= self._temperature_factor()
        else:
            engine_target_rpm = 0.0

        target_rpm = max(starter_target_rpm, engine_target_rpm)

        self.rpm = int(target_rpm + (self.rpm - target_rpm) * math.exp(-0.2 / self.T1))

        if target_rpm == 0:
            target_celcius = 0.0
        else:
            target_celcius = self.MAX_SIMULATED_TEMPERATURE_CELSIUS * (0.5 + 0.5 * gas_throttle_pct / 100)

        self.temperature_celsius = target_celcius + (self.temperature_celsius - target_celcius) * math.exp(-0.2 / self.T2)

    def get_temperature_kelvin(self) -> float:
        return self.temperature_celsius + 273.15

    def _temperature_factor(self):
        if self.temperature_celsius < self.COLD_TRESHOLD_CELCIUS:
            return max(0.5, self.temperature_celsius / self.COLD_TRESHOLD_CELCIUS)

        if self.temperature_celsius >= self.HOT_TRESHOLD_CELCIUS and self.temperature_celsius < self.CRITICAL_TRESHOLD_CELSIUS:
            overheat_amount = self.temperature_celsius - self.HOT_TRESHOLD_CELCIUS
            max_overheat_amount = self.CRITICAL_TRESHOLD_CELSIUS - self.HOT_TRESHOLD_CELCIUS
            return max(0.8, 1.0 - 0.2 * overheat_amount / max_overheat_amount)

        if self.temperature_celsius >= self.CRITICAL_TRESHOLD_CELSIUS:
            self.failure_deadline = time.time() + 10.0
            return 0.0

        return 1.0

    def __str__(self):
        return (f"Engine(rpm={self.rpm}, "
                f"temperature={int(self.temperature_celsius)}°C)")


class Sim:
    ICE_STATUS_PUB_RATE_HZ = 5.0
    def __init__(self, port: Optional[str], node_id: int):
        self.controller = Controller()
        self.engine = Engine()

        self.node = Sim._create_dronecan_node(port, node_id)

        self.node.mode = dronecan.uavcan.protocol.NodeStatus().MODE_OPERATIONAL
        self.node.add_handler(dronecan.uavcan.equipment.esc.RawCommand, self._gas_throttle_callback)
        self.node.add_handler(dronecan.uavcan.equipment.actuator.ArrayCommand, self._air_throttle_callback)

        self.msg = dronecan.uavcan.equipment.ice.reciprocating.Status()

    def spin_once(self):
        if time.time() > self.controller.in_gas_throttle_timestamp + 0.5:
            self.controller.in_gas_throttle_pct = 0

        # Simulate the controller behaviour (ice node)
        self.controller.update_controller(self.engine.rpm)
        logger.info(self.controller)

        # Simulate the engine behaviour (DLE-20 or DLE-35)
        self.engine.update_engine(self.controller.out_gas_throttle_pct,
                                  self.controller.out_air_throttle_pct,
                                  self.controller.out_starter_enabled,
                                  self.controller.out_spark_ignition_enabled)
        logger.info(self.engine)

        self.msg.state = self.controller.state
        self.msg.engine_load_percent = self.controller.out_gas_throttle_pct
        self.msg.engine_speed_rpm = self.engine.get_noisy_rpm()
        self.msg.throttle_position_percent = self.controller.out_air_throttle_pct
        self.msg.spark_plug_usage = self.controller.out_spark_ignition_enabled
        self.msg.oil_temperature = self.engine.get_temperature_kelvin()
        self.msg.coolant_temperature = self.controller.get_internal_stm32_temperature_kelvin()
        self.msg.intake_manifold_pressure_kpa = self.controller.get_voltage_5v()
        self.msg.oil_pressure = self.controller.get_voltage_vin()

        self.node.broadcast(self.msg)
        self.node.spin(1.0 / self.ICE_STATUS_PUB_RATE_HZ)

    def _gas_throttle_callback(self, event: dronecan.node.TransferEvent):
        if len(event.message.cmd) >= 8:
            in_gas_throttle_pct = round(event.message.cmd[7] * 100 / 8191.0)
            in_gas_throttle_pct = max(0, min(in_gas_throttle_pct, 100))
            self.controller.set_gas_throttle_pct(in_gas_throttle_pct)

    def _air_throttle_callback(self, event: dronecan.node.TransferEvent):
        for actuator_command in event.message.commands:
            if actuator_command.actuator_id == 10:
                in_air_throttle_pct = int((actuator_command.command_value - 1000) * 0.1)
                self.controller.in_air_throttle_pct = max(0, min(in_air_throttle_pct, 100))

    @staticmethod
    def _create_dronecan_node(port: Optional[str], node_id: int):
        node_info = dronecan.uavcan.protocol.GetNodeInfo.Response()
        node_info.name = 'co.rl.sim_ice'
        if port is None:
            try:
                node = dronecan.make_node('slcan0', node_id=node_id, bitrate=1000000, baudrate=1000000, node_info=node_info)
            except OSError:
                try:
                    node = dronecan.make_node('slcan:/dev/ttyACM0', node_id=node_id, bitrate=1000000, baudrate=1000000, node_info=node_info)
                except OSError:
                    logger.error("Neither slcan0 or /dev/ttyACM0 do exist. Can't create DroneCAN node.")
                    sys.exit(1)
        else:
            node = dronecan.make_node(port, node_id=node_id, bitrate=1000000, baudrate=1000000, node_info=node_info)

        return node

def main(port: Optional[str], node_id: int):
    sim = Sim(port, node_id)

    while True:
        sim.spin_once()

if __name__ =="__main__":
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.ERROR
    )
    logger.setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port",
                        default=None,
                        type=str,
                        help="CAN device name. Examples: slcan:/dev/ttyACM0, slcan0")
    parser.add_argument("--node-id",
                        default=40,
                        type=str,
                        help="Node ID from 1 to 127")
    args = parser.parse_args()

    try:
        main(args.port, args.node_id)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")
