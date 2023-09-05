"""
This script sends RawMessage to node to test servo motor life.
To run this script you must first create an slcan from the serial port with the specified name.
For example, the name 'can0' has been used.
"""
import time
from argparse import ArgumentParser
import dronecan
from dronecan import uavcan

# get command line arguments
parser = ArgumentParser(description='Sends RawCommand')
parser.add_argument("--port", default='can0', type=str, help="CAN interface name")
parser.add_argument("--duration", default='0', type=str,
                    help="time till script shutdown, 0 means that it won't stop")
parser.add_argument("--timeout", default='2', type=str,
                    help="time duration between max and min position of servomotor")

args = parser.parse_args()

node = dronecan.make_node(args.port, node_id=105, bitrate=1000000)

start_time = time.time()
i = [8191, 0, 0, 0, 0, 0, 0, 0]  # First message


def do_publish():
    """
    Function to publish RawCommand. 'i' is a variable,
    that switches globally at the end of this script
    """
    msg = uavcan.equipment.esc.RawCommand(cmd=i)
    node.broadcast(msg)


node.periodic(1 / 15, do_publish)


def switch_data():
    """
    Switches messages and spin node for desired time
    :param i: data of message that affects on do_publish function
    :return:
    """
    global i
    i = [8191, 0, 0, 0, 0, 0, 0, 0]
    node.spin(timeout=int(args.timeout))
    i = [0, 0, 0, 0, 0, 0, 0, 0]
    node.spin(timeout=int(args.timeout))


if args.duration == '0':  # If duration is '0' then script never ends
    while True:
        switch_data()
else:
    while start_time + int(args.duration) > time.time():
        switch_data()