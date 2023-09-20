# GPS_MAG_BARO

## U-center with Cyphal GNSS

1. Install wine for ubuntu.
2. Download [u-center](https://www.u-blox.com/en/product/u-center) (tested with u-center 23.08)
3. Run u-center: `wine64 u-centersetup_v23.08/u-center_v23.08.exe`
4. Compile DSDL, configure SLCAN and Cyphal related environment variables: `cyphal/ds015.sh`
5. Run the script: `python3 nodes/gnss/ublox_center.py`
6. Press Receiver - > Connection -> Network connection

    ![](https://github.com/PonomarevDA/tools/blob/docs/assets/gnss/ucenter/network_connection.png?raw=true)
7. Add new connection `tcp://127.0.0.1:2001`

    ![](https://github.com/PonomarevDA/tools/blob/docs/assets/gnss/ucenter/address.png?raw=true)


## Setup

The following script automatically:

1. Downloads the latest required firmware and upload it to the target
2. Retrive the board data (software version, hardware, UID) and provides auto test of GNSS, Magnetometer and Barometer
3. Optionally, sends report to the printer (tested with XPRINTER XP-365B)

```
./nodes/gnss/setup.sh --protocol <>
```

For details type `--help` option.
