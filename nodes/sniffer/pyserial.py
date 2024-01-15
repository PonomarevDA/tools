#!/usr/bin/env python3
import serial

CMD_EMPTY = b'\r'
CMD_CLOSE_CHANNEL = b'C\r'
CMD_SET_SPEED = b'S8\r'
CMD_OPEN_CHANNEL = b'O\r'
CMD_CLEAR_ERROR_FLAGS = b'F\r'

with serial.Serial("/dev/ttyACM0", 1000000, timeout=1) as ser:
    commands = [CMD_EMPTY,
                CMD_CLOSE_CHANNEL,
                CMD_SET_SPEED,
                CMD_OPEN_CHANNEL,
                CMD_CLEAR_ERROR_FLAGS]
    for cmd in commands:
        # Skip wait for ACK part here for simplicity
        ser.write(cmd)
        print(f"Send {cmd}, recv: {ser.read(1)}")

    can_frame = ""
    for _ in range(300):
        byte = ser.read(1)
        can_frame += byte.decode('utf-8').replace('\r', '\\r')
        if byte == b'\r':
            if can_frame[0] == 'T':
                print(f"recv CAN-frame: {can_frame}")
            can_frame = ''

    ser.write(CMD_CLOSE_CHANNEL)
