# sim_battery.py

The cross-platform way is to use [CAN over serial]([https://python-can.readthedocs.io/en/master/interfaces/slcan.html](https://python-can.readthedocs.io/en/master/interfaces/slcan.html)):

```bash
python3 dronecan/sim_battery.py slcan:/dev/ttyACM0
```

Alternatively, Linux users can use SocketCAN:

```bash
./can/create_slcan.sh
python3 dronecan/sim_battery.py slcan0
```
