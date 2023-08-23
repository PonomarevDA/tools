#!/usr/bin/env python3
from argparse import ArgumentParser
from serial import Serial

def main(port):
    ser = Serial(port, 57600)

    recv_msg = b""
    while True:
        recv_byte = ser.read(1)
        recv_msg += recv_byte
        if recv_byte == b"\n":
            ser.write(recv_msg)
            print(recv_msg.decode(), end="", flush=True)
            recv_msg = b""

if __name__ =="__main__":
    parser = ArgumentParser(description='dump Node Status messages')
    parser.add_argument("--port", default='/dev/ttyUSB1', type=str, help="Serial port")
    args = parser.parse_args()

    main(args.port)
