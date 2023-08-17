#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path

CYPHAL_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent / "cyphal"
sys.path.append(CYPHAL_DIR.absolute().as_posix())

from ubx_cmd import UbloxCommands
from forwarder import SerialForwarder


def main(protocol, interface, config):
    command_generator = UbloxCommands()

    commands = []
    commands.append(command_generator.factory_reset())
    # commands.append(command_generator.change_baudrate_m8(38400))

    if protocol == "cyphal":
        SerialForwarder(node_id=50).run(commands, False, False, sub_verbose=False)
    else:
        print(f"Error: protocol `{protocol}` is not surrpoted.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--protocol", help="Options: cyphal, dronecan, serial", default='cyphal')
    parser.add_argument("-s", "--interface", help="can0, slcan0, /dev/ttyACM0, COM15, ttyS0, etc", default='slcan0')
    parser.add_argument("-o", "--config", help="Config file with commands")
    args = parser.parse_args()

    main(args.protocol, args.interface, args.config)
