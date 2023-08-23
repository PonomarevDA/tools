#!/usr/bin/env python3
from serial import Serial
#Serial takes these two parameters: serial device and baudrate
import time

s = Serial('COM4', 57600, timeout=3)
i=0

while(True):

    d = s.read()
    print(d.decode(),end="", flush=True)
    s.write(d)
