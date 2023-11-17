# Cyphal/CAN tools

## Specification checker

Test cases:

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
