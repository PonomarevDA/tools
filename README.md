[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=PonomarevDA_tools&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=PonomarevDA_tools) [![cyphal_init.sh](https://github.com/PonomarevDA/tools/actions/workflows/cyphal_init.yml/badge.svg)](https://github.com/PonomarevDA/tools/actions/workflows/cyphal_init.yml) [![specification_checker.py](https://github.com/PonomarevDA/tools/actions/workflows/specification_checker.yml/badge.svg)](https://github.com/PonomarevDA/tools/actions/workflows/specification_checker.yml)

# Cyphal/DroneCAN nodes tools  

`tools` is a collection of scripts for testing and configuration of Cyphal/CAN and DroneCAN nodes.

> This package is under development.

## 1. INSTALLATION

**1. Install the package from pypi, test.pypi or from sources**

```bash
pip install raccoonlab-tools
```
```bash
pip install -i https://test.pypi.org/simple/ raccoonlab-tools
```
```bash
git clone https://github.com/PonomarevDA/tools.git
cd tools
pip install .
```

**2. Install dependencies**

If you already have a Cyphal in your system, you probably don't need to install anything additional and have your own way of handling the environment variables and DSDL. Just check [scripts/ubuntu.sh](scripts/ubuntu.sh) script in case if you miss something.

But if you use Cyphal for the first time or deploy a project in a new system, consider to run [scripts/ubuntu.sh](scripts/ubuntu.sh) script. This script:
1. Install all recommended dependencies,
2. Clone recommended DSDL to `~/.cyphal` directory,
3. Create in `~/.cyphal` directory a `setup.sh` script that configure cyphal related environment variables and append `source $HOME/cyphal/setup.sh` to the end of your `.bashrc` file, so your shell will automatically setup the environment variables.

```bash
# By default, it installs both Cyphal and DroneCAN dependencies:
./scripts/ubuntu.sh

# Try --help option to get usage details. It allows to perform more precise installation:
./scripts/ubuntu.sh --help
```

<details><summary>Click here for details about which environment variables are required for a Cyphal application</summary>

To start with Cyphal/CAN (pycyphal, yakut, yukon) the following environment variables should be configured:

| Environment variable | Meaning |
| -------------------- | - |
| CYPHAL_PATH          | Path to DSDL. Let's use the default:`$HOME/.cyphal` |
| UAVCAN__NODE__ID     | The application node identifier |
| UAVCAN__CAN__IFACE   | CAN iface name |
| UAVCAN__CAN__BITRATE | Arbitration/data segment bits per second |
| UAVCAN__CAN__MTU     | Maximum transmission unit: 8 for classic CAN |

> Check pycyphal/yakut/yukon docs for additional details

</details>

## 2. LINUX PREPARATION (SOCKETCAN)

By default, DroneCAN and Cyphal/CAN uses cross-platform transport interface [Python-CAN](https://python-can.readthedocs.io/en/stable/) [CAN over Serial / SLCAN](https://python-can.readthedocs.io/en/stable/interfaces/slcan.html).

On Linux, [the socketcan interface](https://python-can.readthedocs.io/en/stable/interfaces/socketcan.html) is recommended. Unlike SLCAN, socketcan interface allows to share the same CAN interface with multiple processes, so you can run a few pycyphal scripts, yukon, yakut simultaniously.

You can run the following script:

```bash
./scripts/socketcan.sh
```

For a Cyphal application after creating socketcan interface, you need to update `UAVCAN__CAN__IFACE` environment variable. Just call `source ~/.bashrc`.

## 3. USAGE

### 1. Test cyphal specification

```bash
rl-test-cyphal-specification
```

![](https://github.com/PonomarevDA/tools/blob/docs/assets/cyphal/specification_checker.gif?raw=true)

### 2. Test dronecan specification

```bash
rl-test-dronecan-specification
```

```bash
rl-test-dronecan-gps-mag-baro
```

![](https://github.com/PonomarevDA/tools/blob/docs/assets/rl-test-dronecan-specification.gif?raw=true)


### 3. Get Node Info (Cyphal / DroneCAN)

```bash
rl-get-info
```

Return:
- Online CAN-sniffers
- Detect protocol if any CAN-node is avaliable: cyphal | dronecan | none
- Show node info of Cyphal/CAN or DroneCAN node if it is avaliable

### 4. Upload firmware with st-link linux / STM32CubeProgrammer Windows

```bash
rl-upload-firmware --config PATH_TO_YAML_CONFIG
```

```bash
rl-upload-firmware --binary PATH_TO_BIN_FILE
```

There are a few ways how you can specify the path to the binary:

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

4. Direct .bin path with `--binary` option

### 5. Upload config

```bash
rl-config --config PATH
```

Example of yaml config file:

```yaml
# config.yaml
params:
    uavcan.node_id: 31
    uavcan.node.name: co.rl.mini
```

![](https://github.com/PonomarevDA/tools/blob/docs/assets/rl-config.gif?raw=true)


### 6. Monitor

```bash
rl-monitor
```

This script is used for automated node analysis. Within a single command:
- detect the protocol (Cyphal or DroneCAN),
- detect the node type,
- check the software version and highlight if it is not the latest,
- configure it if it has not been configured yet,
- subscribes on all possible topics,
- provide basic tests and diagnostics, highlight issues,
- publish some test commands if possible,
- print all data in real time.

An example of `rl-monitor` with gnss node:

![](https://github.com/PonomarevDA/tools/wiki/assets/monitor_gnss.gif)

### 7. U-center with Cyphal GNSS

```bash
rl-ublox-center
```

For RL GNSS it is possible to run u-center over Cyphal via `gps.ubx_tx` and `gps.ubx_rx` topics.

1. Download [u-center](https://www.u-blox.com/en/product/u-center) (tested with u-center 23.08)
2. Run the u-center. On ubuntu you can use wine (`wine64 u-centersetup_v23.08/u-center_v23.08.exe`)
3. Configure the Cyphal environment
4. Run the script `rl-ublox-center`
5. Press Receiver - > Connection -> Network connection
6. Add new connection `tcp://127.0.0.1:2001`

An illustration:

![](https://github.com/PonomarevDA/tools/blob/docs/assets/gnss/ucenter/network_connection.png?raw=true)

![](https://github.com/PonomarevDA/tools/blob/docs/assets/gnss/ucenter/address.png?raw=true)

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

## 4. DEVELOPER NOTES

Deploy to [TestPyPI](https://test.pypi.org/project/raccoonlab-tools/):

```bash
./scripts/deploy.sh
```

Deploy to [PyPI](https://pypi.org/project/raccoonlab-tools/):

```bash
./scripts/deploy.sh --pypi
```

## 5. USAGE TERMS

The scripts are distributed under MIT license. In general, you can do with them whatever you want. If you find a bug, please suggest a PR or an issue.
