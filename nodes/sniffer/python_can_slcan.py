#!/usr/bin/env python3
import can
with can.Bus(interface='slcan', channel='/dev/ttyACM0', ttyBaudrate=1000000, bitrate=1000000) as bus:
    for _ in range(10):
        msg = bus.recv()
        print(msg)
