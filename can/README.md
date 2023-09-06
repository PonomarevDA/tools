# CAN tools

**Install**

```bash
./can/install.sh
```

**Create CAN interface based on serial CAN device**

```bash
./can/create_slcan_from_serial.sh --help
```

**Create Virtual CAN interface**

```bash
./can/vcan.sh --help
```

# Notes

## CAN over Serial

Reference: [hhttps://python-can.readthedocs.io/en/master/interfaces/serial.html](https://python-can.readthedocs.io/en/master/interfaces/serial.html).

| | Start byte | Timestamp | DLC | ID | Payload | End byte |
|-| ---------- | --------- | --- | -- | ------- | -------- |
| | 1          | 4         | 1   | 4  | 0-8     | 1        |
| | 0xAA       | 4         | 1   | 4  |         | 0xBB     |

Empty frame is 11 bytes length, 8-byte frame is 19 bytes length.

## CAN over Serial / SLCAN (LAWICEL)

Reference: [https://python-can.readthedocs.io/en/master/interfaces/slcan.html](https://python-can.readthedocs.io/en/master/interfaces/slcan.html).

| | Start byte | ID | Size | Payload | End byte |
|-| ---------- | -- | ---- | ------- | -------- |
| | 1          | 8  | 1    | 0-16    | 1        |
| | 'T'        |    |      |         | '\r'     |

Empty frame is 11 bytes length, 8-byte frame is 27 bytes length.
