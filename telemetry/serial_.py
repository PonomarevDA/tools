#!/usr/bin/env python3
from serial import Serial
#Serial takes these two parameters: serial device and baudrate
import time

from datetime import datetime

s = Serial('COM5', 57600)
i=0

buff = b''

old_t = 0

while(True):

    now = datetime.now()
    t = datetime.timestamp(now)
    #time.sleep(0.001)

    if( t > old_t+0.1 ):
        #print(t)
        #named_tuple = time.localtime() # get struct_time
        #time_string = time.strftime("%H:%M:%S", named_tuple)

        msg = f'[{i}] [{now}] HELLO\r\n'.encode()
        #output = msg.serialize()
        s.write(msg)
        i+=1
        old_t = t

    #d = s.read()
    
    #buff += d
    #
    #if len(buff)>200:
    #    print(buff.decode(),end="", flush=True)
    #    buff=b''


    #s.write(d)

    #time.sleep(0.5)
    #i+=0.5
