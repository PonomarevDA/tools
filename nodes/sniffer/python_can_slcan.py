#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import can
with can.Bus(interface='slcan', channel='/dev/ttyACM0', ttyBaudrate=1000000, bitrate=1000000) as bus:
    for _ in range(10):
        msg = bus.recv()
        print(msg)
