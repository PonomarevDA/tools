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
