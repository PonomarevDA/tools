# lights_tester
The cross-platform way is to use CAN over serial:

```bash
python3 dronecan/lights_tester.py slcan:/dev/ttyACM0
```
Alternatively, Linux users can use SocketCAN:

```bash
./can/create_slcan.sh
python3 dronecan/lights_tester.py slcan0
```