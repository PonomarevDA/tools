# uavcan_tools

This repository is a set of tools for Cyphal and DroneCAN applications.

It is intended for use with [RaccoonLab CAN-sniffer](https://docs.raccoonlab.co/guide/programmer_sniffer/) with Ununtu 20.04 or newer.

## Cyphal usage

The following script automatically:
1. Create SLCAN based on CAN-sniffer
2. Configure environment variables if they are not already configured
3. Compile DSDL based on public regulated data types

```bash
./src/cyphal/init.sh --help
```

> The script expects you have clonned [public_regulated_data_types](https://github.com/OpenCyphal/public_regulated_data_types) inside this repository. It will compile everything into `compile_output` directory and create interface with name `slcan0`. You can override these parameters by manually setting the following environment variables: `REG_DATA_TYPE_PATH`, `YAKUT_COMPILE_OUTPUT`, `UAVCAN__CAN__IFACE`.

## DroneCAN usage

Creare SLCAN:

```bash
./src/can/create_slcan_from_serial.sh --help
```
