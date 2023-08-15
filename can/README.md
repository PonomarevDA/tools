# CAN tools

## Create CAN interface over serial CAN device

```bash
sudo apt-get install can-utils

./can/create_slcan_from_serial.sh --help
```

## Create Virtual CAN interface

```bash
sudo apt-get install -y linux-modules-extra-$(uname -r)
python3 -m pip install yakut

./can/vcan.sh slcan0
```

## CAN over Serial

Reference: [hhttps://python-can.readthedocs.io/en/master/interfaces/serial.html](https://python-can.readthedocs.io/en/master/interfaces/serial.html).

| | Start byte | Timestamp | DLC | ID | Payload | End byte |
|-| ---------- | --------- | --- | -- | ------- | -------- |
| | 1          | 4         | 1   | 4  | 0-8     | 1        |
| | 0xAA       | 4         | 1   | 4  |         | 0xBB     |

Empty frame is 11 bytes length, full frame is 19 bytes length.

## CAN over Serial / SLCAN (LAWICEL)

Reference: [https://python-can.readthedocs.io/en/master/interfaces/slcan.html](https://python-can.readthedocs.io/en/master/interfaces/slcan.html).

| | Start byte | ID | Size | Payload | End byte |
|-| ---------- | -- | ---- | ------- | -------- |
| | 1          | 8  | 1    | 0-16    | 1        |
| | 'T'        |    |      |         | '\r'     |

Empty frame is 11 bytes length, full frame is 27 bytes length.
