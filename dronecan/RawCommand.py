import time
from argparse import ArgumentParser
import dronecan
from dronecan import uavcan

# get command line arguments
parser = ArgumentParser(description='Sends RawCommand')
parser.add_argument("--port", default='can0', type=str, help="CAN interface name")
parser.add_argument("--time", default=0, type=str,
                    help="time till script shutdown, 0 means that it won't stop")

args = parser.parse_args()

node = dronecan.make_node(args.port, node_id=105, bitrate=1000000)

while True:

    for i in [[8191, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]]:
        print('new spin started')
        # print(i)
        def do_publish():
            msg = uavcan.equipment.esc.RawCommand(cmd=i)
            node.broadcast(msg)

            print('publishing')

        node.periodic(1/10, do_publish)
        node.spin(timeout=2)