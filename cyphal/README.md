# Cyphal/CAN tools

A few Cyphal related scripts are collected here.


## 1. cyphal/init.sh

The script automatically:

1. Create SLCAN based on CAN-sniffer or create virtual CAN inreface
2. Configure environment variables if they are not already configured (`UAVCAN__CAN__IFACE`, `UAVCAN__CAN__MTU`, `UAVCAN__NODE__ID`, `YAKUT_PATH`)
3. Compile DSDL based on public regulated data types and ds015

Install dependencies:

```bash
sudo apt-get install can-utils
python3 -m pip install yakut
```

Clone [PonomarevDA/tools](https://github.com/PonomarevDA/tools.git) repository and [OpenCyphal/public_regulated_data_types](https://github.com/OpenCyphal/public_regulated_data_types) in the same folder:

```bash
git clone https://github.com/PonomarevDA/tools.git
cd tools
git clone https://github.com/OpenCyphal/public_regulated_data_types.git
```

Let's say, your CAN-interface is not initialized yet. You can check it with `ifconfig`. You can delete it with `sudo ip link delete slcan0`. Normally, you don't need to delete it, but let's keep this command here just in case.

If you want to create SLCAN based on a real CAN-sniffer such as [RaccoonLab CAN-sniffer and STM32 programmer](https://docs.raccoonlab.co/guide/programmer_sniffer/) or [Zubax Babel-Babel](https://shop.zubax.com/products/zubax-babel-babel-all-in-one-debugger-for-robotics-drone-development), you can type:

```bash
source cyphal/init.sh -i slcan0 -n 127 # All options in the command are actually defaults, so you can skip them
```

If you want to run it without a real CAN-sniffer hardware, you can run the following command:

```bash
source cyphal/init.sh -i slcan0 -n 127 -v
```

![](https://github.com/PonomarevDA/tools/blob/docs/assets/cyphal/cyphal_init.gif?raw=true)

For additional usage details please type:

```bash
source cyphal/init.sh --help
```

For usage example without a real hardware you can also check the workflows:
- [.github/workflows/cyphal_init.yml](../.github/workflows/cyphal_init.yml)
- [.github/workflows/specification_checker.yml](../.github/workflows/specification_checker.yml)


## 2. specification_checker.py

The script follows the test cases in the table below:

| № | Name                   | Test case description |
| - | ---------------------- | --------------------- |
| 1 | Node name              | 1. Request GetInfo </br> 2. Parse response: the name must follow the pattern
| 2 | Heartbeat frequency    | 1. Listen for Heartbeat for 5 seconds </br> 2. Check min and max timeouts between messages. The frequency should be 1 Hz.
| 3 | Persistent memory      | 1. y r <id> uavcan.node.description <random_string> </br> 2. y cmd <id> 65530 </br> 3. y cmd <id> 65535 </br> 4. y r <id> uavcan.node.description # <random_string>
| 4 | Port.List              | 1. Wait <= 10 seconds for port.List </br> 2. Check response: at least 384, 385, 430, 435 ports must be supported
| 5 | Registers name         | 1. Request all registers </br> 2. Parse responses: the name must follow the pattern
| 6 | Default registers existance | 1. Request "uavcan.node.id" register </br> 2. Request "uavcan.node.description" register
| 7 | Port register type     | 1. Request all registers </br> 2. Select port related registers </br> 3. All `uavcan.*.id` registers are natural16, mutable and persistent </br> 4. All `uavcan.*.type` registers are string, immutable and persistent

Assumptions for all nodes:
- there is only one node only online and her ID != 127

Usage:

```bash
source cyphal/ds015.sh
pytest cyphal/specification_checker.py --verbose
```

![](https://github.com/PonomarevDA/tools/blob/docs/assets/cyphal/specification_checker.gif?raw=true)
