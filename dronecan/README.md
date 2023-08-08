# DroneCAN

If you have [RaccoonLab CAN-sniffer and STM32 programmer](https://docs.raccoonlab.co/guide/programmer_sniffer/), you should type:

```bash
./can/create_slcan_from_serial.sh
python3 dronecan/sim_battery.py slcan0
```

With other CAN-sniffer it might be something like:

```bash
python3 dronecan/sim_battery.py /dev/ttyACM0
```
