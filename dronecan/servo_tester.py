#!/usr/bin/env python3
"""
This script sends RawMessage to node to test servo motor life.
To run this script you must first create an slcan from the serial port with the specified name.
For example, the name 'can0' has been used.
"""
import datetime
import time
from argparse import ArgumentParser
import dronecan
from dronecan import uavcan

# get command line arguments
parser = ArgumentParser(description='Sends RawCommand')
parser.add_argument("--port", default='can0', type=str, help="CAN interface name")
parser.add_argument("--duration", default='0', type=str,
                    help="time till script shutdown, 0 means that it won't stop")
parser.add_argument("--timeout", default='0.5', type=str,
                    help="time duration between max and min position of servomotor")

args = parser.parse_args()

node = dronecan.make_node(args.port, node_id=105, bitrate=1000000)

start_time = time.time()
i = [1614, 0, 0, 0, 0, 0, 0, 0]  # First message


def do_publish():
    """
    Function to publish RawCommand. 'i' is a variable,
    that switches globally at the end of this script
    """
    msg = uavcan.equipment.esc.RawCommand(cmd=i)
    node.broadcast(msg)


message = ''
node.periodic(1 / 15, do_publish)
MOVE_COUNTER = 0


def handle_node_info(msg):
    global message
    message = (f"Uptime: {datetime.timedelta(seconds=int(str(dict(msg.transfer.payload._fields)['uptime_sec'])))}, " +
               f"Health: {dict(msg.transfer.payload._fields)['health']}")


node.add_handler(uavcan.protocol.NodeStatus, handle_node_info)


def switch_data():
    """
    Switches messages and spin node for desired time
    :param i: data of message that affects on do_publish function
    :return:
    """
    event_time = datetime.timedelta(seconds=int(time.time() - start_time))
    try:
        global i, MOVE_COUNTER, message
        i = [7000, 0, 0, 0, 0, 0, 0, 0]
        node.spin(timeout=float(args.timeout))
        i = [100, 0, 0, 0, 0, 0, 0, 0]
        node.spin(timeout=float(args.timeout))
        MOVE_COUNTER += 2
        file = open('result.txt', 'w')
        print(f'Movements: {MOVE_COUNTER}, {message}', file=file)
    except dronecan.driver.common.TxQueueFullError:
        print('Exception dronecan.driver.common.TxQueueFullError catched', event_time)
    except dronecan.transport.TransferError:
        print('Exception dronecan.transport.TransferError catched', event_time)
    except Exception as err:
        print(err, event_time)


if args.duration == '0':  # If duration is '0' then script never ends
    while True:
        switch_data()
else:
    while start_time + int(args.duration) > time.time():
        switch_data()
