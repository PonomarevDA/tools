import dronecan, datetime, time
from dronecan import uavcan
from argparse import ArgumentParser
import pandas as pd

# get command line arguments
parser = ArgumentParser(description='dump Node Status messages')
parser.add_argument("--port", default='can0', type=str, help="serial port")
parser.add_argument("--outfile", default='output', type=str, help="name of file where output will be stored")
parser.add_argument("--logtime", default=3600, type=int, help="Logging duration in seconds"
                                                              "3600 means the script will collect and summarise messages for one hour")
args = parser.parse_args()

# Initializing a DroneCAN node instance.
node = dronecan.make_node(args.port, bitrate=1000000)

# Initializing a node monitor, so we can see what nodes are online
node_monitor = dronecan.app.node_monitor.NodeMonitor(node)

data = []
finalDF = pd.DataFrame()
columnnames = ['Date', 'Node id', 'Uptime', 'Health']


def handle_node_info(msg):
    '''
        Function is used in add_handler method. Handle message in format of csv
        :param msg:
        :return:
        '''
    data.append(['{} {}'.format(datetime.date.today().strftime("%d/%m/%Y"),
                                (datetime.datetime.now() + datetime.timedelta(hours=2)).strftime("%H:%M:%S")),
                 msg.transfer.source_node_id,
                 datetime.timedelta(
                     seconds=int(str(dict(msg.transfer.payload._fields)['uptime_sec']))),
                 dict(msg.transfer.payload._fields)['health']])


node.add_handler(uavcan.protocol.NodeStatus, handle_node_info)


def spin_node():
    now = time.time()
    while now + args.logtime > time.time():
        try:
            node.spin(timeout=args.logtime)  # spin node for hour and gathering dataset

        except Exception as ex: # Print all errors if node gives broken message
            print(ex)


while True:
    try:
        print('Listening nodes... : ', (datetime.datetime.now() + datetime.timedelta(hours=2)).strftime("%H:%M:%S"))
        data = []
        spin_node()
        df = pd.DataFrame(data, columns=columnnames)

        listid = list(df['Node id'].unique())

        for i in listid:
            finalDF = finalDF._append(pd.DataFrame(data=[[df['Date'][df['Node id']==i].iloc[-1],
                                                          i,
                                                          df['Uptime'][df['Node id']==i].iloc[-1],
                                                          df['Health'][df['Node id']==i].iloc[-1]
                                                          ]]
                                                   )
                                      )
        # finally save to csv
        finalDF.to_csv(args.outfile + '.csv', header=False, index=False)
    except Exception:
        pass