[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=PonomarevDA_tools&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=PonomarevDA_tools) [![cyphal_init.sh](https://github.com/PonomarevDA/tools/actions/workflows/cyphal_init.yml/badge.svg)](https://github.com/PonomarevDA/tools/actions/workflows/cyphal_init.yml) [![specification_checker.py](https://github.com/PonomarevDA/tools/actions/workflows/specification_checker.yml/badge.svg)](https://github.com/PonomarevDA/tools/actions/workflows/specification_checker.yml)

# Cyphal/DroneCAN nodes tools  

`tools` is a collection of scripts for testing and configuration of Cyphal/CAN and DroneCAN nodes.

> This package is under development. It is avaliable in [test.pypi](https://test.pypi.org/project/raccoonlab-tools/) at the moment.

## Preparation

1. Install the package either from test.pypi or from sources:
    ```bash
    pip install -i https://test.pypi.org/simple/ raccoonlab-tools
    ```
    ```bash
    git clone https://github.com/PonomarevDA/tools.git
    cd tools
    pip install .
    ```
2. Clone the nodes config files somewhere. We recommend `~/.raccoonlab_tools/vendors` For example:
    ```bash
    mkdir -p ~/.raccoonlab_tools/vendors/raccoonlab
    cd ~/.raccoonlab_tools/vendors/raccoonlab
    git clone https://github.com/RaccoonlabDev/raccoonlab_nodes_configs.git .
    ```
3. Install additional dependencies if you want to upload a firmware with STM32-programmer:
    - On ubuntu install [stlink](https://github.com/stlink-org/stlink),
    - On Windows install [STM32CubeProgrammer](https://www.st.com/en/development-tools/stm32cubeprog.html) to the default directory.

4. Before working with a Cyphal node, you should configure the Cyphal-related environment variables.
Check Cyphal for help. You can use [scripts/cyphal](scripts/cyphal) as a hint.

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

## Developer notes

Deploy to [TestPyPI](https://test.pypi.org/project/raccoonlab-tools/):

```bash
./scripts/deploy.sh
```

Deploy to [PyPI](https://pypi.org/project/raccoonlab-tools/):

```bash
./scripts/deploy.sh --pypi
```

## License

The scripts are distributed under MIT license. In general, you can do with them whatever you want. If you find a bug, please suggest a PR or an issue.
