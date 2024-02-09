[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=PonomarevDA_tools&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=PonomarevDA_tools) [![cyphal_init.sh](https://github.com/PonomarevDA/tools/actions/workflows/cyphal_init.yml/badge.svg)](https://github.com/PonomarevDA/tools/actions/workflows/cyphal_init.yml) [![specification_checker.py](https://github.com/PonomarevDA/tools/actions/workflows/specification_checker.yml/badge.svg)](https://github.com/PonomarevDA/tools/actions/workflows/specification_checker.yml)

# Cyphal/DroneCAN nodes tools  

`tools` is a collection of scripts for testing and configuration of Cyphal/CAN and DroneCAN nodes.

## Current status

> This package is under development. It is avaliable in [test.pypi](https://test.pypi.org/project/raccoonlab-tools/) at the moment.

## Usage

Install the package from test.pypi and then run the desired script:

```
pip install -i https://test.pypi.org/simple/ raccoonlab-tools
```

### 1. Test cyphal specification

```bash
rl-test-cyphal-specification
```

![](https://github.com/PonomarevDA/tools/blob/docs/assets/cyphal/specification_checker.gif?raw=true)

### 2. Test dronecan specification

```bash
rl-test-dronecan-specification
```

![](https://github.com/PonomarevDA/tools/blob/docs/assets/rl-test-dronecan-specification.gif?raw=true)

### 3. Check protocol

```bash
rl-check-protocol
```

return cyphal | dronecan | none

### 4. Upload firmware with st-link linux / STM32CubeProgrammer Windows

```bash
rl-upload-firmware --config PATH
```

There are 3 ways how you can specify the path to the binary:

1. (recommended) Using a GitHub Repository. It will always download the latest released firmware.

```yaml
# config.yaml
metadata:
    link: RaccoonlabDev/mini_v2_node
```

2. Direct Link to the Firmware File

```yaml
# config.yaml
metadata:
    link: https://github.com/RaccoonlabDev/docs/releases/download/v1.6.5/gnss_v2_cyphal_v1.6.5_c78d47c3.bin
```

3. Using a Local Path

```yaml
# config.yaml
metadata:
    link: /user/home/firmwares/node.bin
```

### 5. Upload dronecan parameters

```bash
rl-get-dronecan-params
```

```bash
rl-set-dronecan-params --config PATH
```

Example of yaml config file:

```yaml
# config.yaml
params:
    uavcan.node_id: 31
    uavcan.node.name: co.rl.mini
```

![](https://github.com/PonomarevDA/tools/blob/docs/assets/rl-dronecan-config.gif?raw=true)


### 6. Cyphal monitor

```bash
rl-cyphal-monitor
```

Usage example:

![](https://github.com/PonomarevDA/tools/wiki/assets/monitor_gnss.gif)

<!--

### 6. Upload cyphal parameters

### UC7-8. Check cyphal/dronecan node type by name

rl-give-node-type

### UC9. Check RL firmware version

rl-check-updates

### UC10. Check other (custom) vendors firmware version

...

### UC11-12. Create socketcan linux (real/virtual)

rl-socketcan

### UC13-14. Create slcan linux/windows -->

## License

The scripts are distributed under MIT license. In general, you can do with them whatever you want. If you find a bug, please suggest a PR or an issue.
