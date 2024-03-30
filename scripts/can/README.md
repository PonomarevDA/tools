# CAN tools

Supported CAN-sniffers:
- [RaccoonLab CAN-sniffer and STM32 programmer](https://docs.raccoonlab.co/guide/programmer_sniffer/),
- [Zubax Babel-Babel](https://shop.zubax.com/products/zubax-babel-babel-all-in-one-debugger-for-robotics-drone-development).

## 1. Usage

To create SLCAN based on CAN-sniffer:

```bash
./can/create_slcan.sh
```

To create virtual CAN:

```bash
./can/create_slcan.sh -v
```

## 2. Notes

**slcand**

```bash
#   -o              option means open command
#   -s8             option means 1000 Kbit/s CAN bitrate
#   -t hw           option means UART flow control
#   -S $BAUD_RATE   option means uart baud rate
#   $DEV_PATH       position argument means port name
```

Setup SocketCAN queue discipline type
By default it uses pfifo_fast with queue size 10.
This queue blocks an application when queue is full.
So, we use pfifo_head_drop. This queueing discipline drops the earliest enqueued
packet in the case of queue overflow.
More about queueing disciplines:
https://rtime.felk.cvut.cz/can/socketcan-qdisc-final.pdf

**CAN over Serial**

Reference: [hhttps://python-can.readthedocs.io/en/master/interfaces/serial.html](https://python-can.readthedocs.io/en/master/interfaces/serial.html).

| | Start byte | Timestamp | DLC | ID | Payload | End byte |
|-| ---------- | --------- | --- | -- | ------- | -------- |
| | 1          | 4         | 1   | 4  | 0-8     | 1        |
| | 0xAA       | 4         | 1   | 4  |         | 0xBB     |

Empty frame is 11 bytes length, 8-byte frame is 19 bytes length.

**CAN over Serial / SLCAN (LAWICEL)**

Reference: [https://python-can.readthedocs.io/en/master/interfaces/slcan.html](https://python-can.readthedocs.io/en/master/interfaces/slcan.html).

| | Start byte | ID | Size | Payload | End byte |
|-| ---------- | -- | ---- | ------- | -------- |
| | 1          | 8  | 1    | 0-16    | 1        |
| | 'T'        |    |      |         | '\r'     |

Empty frame is 11 bytes length, 8-byte frame is 27 bytes length.
