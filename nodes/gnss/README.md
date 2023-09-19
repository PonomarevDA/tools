# GPS_MAG_BARO

## U-center

1. Install wine for ubuntu.
2. Download [u-center](https://www.u-blox.com/en/product/u-center) (tested with u-center 23.08)
3. Run u-center: `wine64 u-centersetup_v23.08/u-center_v23.08.exe`
4. Run the script: `python3 nodes/gnss/ublox_center.py`
5. Press Receiver - > Connection -> Network connection

    ![](https://github.com/PonomarevDA/tools/blob/docs/assets/gnss/ucenter/network_connection.png?raw=true)
6. Add new connection `tcp://127.0.0.1:2001`

    ![](https://github.com/PonomarevDA/tools/blob/docs/assets/gnss/ucenter/address.png?raw=true)


## Setup

