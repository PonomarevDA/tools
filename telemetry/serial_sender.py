#!/usr/bin/env python3
from datetime import datetime
import threading
from argparse import ArgumentParser
from serial import Serial

class TelemPeriodicalWriter:
    def __init__(self, ser) -> None:
        self.serial = ser
        self.total_send = 0
        threading.Timer(0.1, self.write_to_telem).start()

    def write_to_telem(self):
        self.total_send += 1
        time_now = datetime.timestamp(datetime.now())
        msg = f'[{self.total_send : >5}] ts1=[{time_now}]\r\n'.encode()
        self.serial.write(msg)
        threading.Timer(0.1, self.write_to_telem).start()

    def get_total_send(self):
        return self.total_send

class TelemReceiver:
    def __init__(self, ser, telem_writer) -> None:
        self.serial = ser
        self.telem_writer = telem_writer

    def spin(self):
        parsed_msg = b''
        while True:
            recv_byte = self.serial.read(1)
            if recv_byte == b"\n":
                parsed_msg += recv_byte
                self.print_and_parse_message(parsed_msg)
                parsed_msg = b""
            else:
                parsed_msg += recv_byte

    @staticmethod
    def print_and_parse_message(raw_msg):
        decoded_buffer = raw_msg.decode()
        if len(decoded_buffer) == 33:
            send_counter = int(decoded_buffer[1:6])
            recv_ts = float(decoded_buffer[13:30])
            time_now = datetime.timestamp(datetime.now())
            delay = time_now - recv_ts
            print(f"{send_counter}: {time_now}, {recv_ts}, delay={int(delay * 1000)} ms")
        else:
            print(f"package is broken, len = {len(decoded_buffer)}")


def main(port):
    ser = Serial(port, 57600)
    telem_writer = TelemPeriodicalWriter(ser)

    telem_receiver = TelemReceiver(ser, telem_writer)
    telem_receiver.spin()


if __name__ =="__main__":
    parser = ArgumentParser(description='dump Node Status messages')
    parser.add_argument("--port", default='/dev/ttyUSB0', type=str, help="Serial port")
    args = parser.parse_args()
    try:
        main(args.port)
    except KeyboardInterrupt:
        pass
