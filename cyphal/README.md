# Cyphal/CAN tools

A few Cyphal related scripts are collected here.

## PREPARATION

To start with Cyphal/CAN (pycyphal, yakut, yukon) the following environment variables should be configured:

| Environment variable | Meaning |
| -------------------- | - |
| CYPHAL_PATH          | Path to DSDL. Let's use the default:`$HOME/.cyphal` |
| UAVCAN__NODE__ID     | The application node identifier |
| UAVCAN__CAN__IFACE   | CAN iface name |
| UAVCAN__CAN__BITRATE | Arbitration/data segment bits per second |
| UAVCAN__CAN__MTU     | Maximum transmission unit: 8 for classic CAN |

There are a few approaches here.

1. If you have a CAN-sniffer ([RL CAN-sniffer](https://docs.raccoonlab.co/guide/programmer_sniffer/) or [Zubax Babel](https://zubax.com/products/babel)) and you want a simple connection to your device, the recommended cross-platform way is to use [Python-CAN](https://python-can.readthedocs.io/en/stable/) [CAN over Serial / SLCAN](https://python-can.readthedocs.io/en/stable/interfaces/slcan.html) interface.

    On Linux you can simply run the following script:

    ```bash
    source cyphal/setup_linux_slcan.sh
    ```

    On Windows you can try [setup.ps1](https://gist.github.com/sainquake/7f06a2425ee54178633eac60f9002608) script.

2. If you have Linux, alternatively you can use [socketcan interface](https://python-can.readthedocs.io/en/stable/interfaces/socketcan.html). Unlike SLCAN, socketcan interface allows to share the same virtual CAN interface with multiple processes, so you run a few pycyphal scripts, yukon, yakut simultaniously.

    <details><summary>Click here for details how to use cyphal/init.sh script to setup CAN interface with socketcan on Linux</summary>

    cyphal/init.sh automatically:

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

    </details>

## CYPHAL SPECIFICATION CHECKER

[specification_checker.py](specification_checker.py) is a collection of pytest tests for a few Application-level functions described in [the Cyphal specification](https://opencyphal.org/specification/Cyphal_Specification.pdf).

All tests are divided into a few groups. A brief their description is shown below.

**5.3.2. Node heartbeat (uavcan.node.Heartbeat)**

| № | Name                   | Test case description |
| - | ---------------------- | --------------------- |
| 1 | test_frequency         | 1. Wait for 5 Heartbeats </br> 2. Check that the publishing rate is exactly 1 Hz |
| 2 | test_uptime            | 1. Wait for 5 Heartbeats </br> 2. Check that the uptime is correctly increased. The node should be rebooted during the test. </br> This test is useful for Watchdog issues detection |

**5.3.3. Generic node information (uavcan.node.GetInfo)**

| № | Name                      | Test case description |
| - | ------------------------- | --------------------- |
| 1 | test_protocol_version     | The Protocol version field should be filled in. |
| 2 | test_hardware_version     | Hardware version field should be filled. |
| 3 | test_software_version     | Software version field should be filled. |
| 4 | test_software_vcs_revision_id  | Software VSC field should be filled. |
| 5 | test_unique_id            | Software UID field should be filled. |
| 6 | test_software_image_crc   | Software Image CRC field should be filled. |
| 7 | test_certificate_of_authenticity  | The certificate of authenticity (COA) field should be filled. |
| 8 | test_node_name            | Node name pattern: com.manufacturer.project.product. |

**5.3.4. Bus data flow monitoring (uavcan.node.port)**

| № | Name                      | Test case description |
| - | ------------------------- | --------------------- |
| 1 | test_reigister_interface_is_supported | port_list.servers.mask[384] </br> port_list.servers.mask[385] |
| 2 | test_get_info_is_supported            | port_list.servers.mask[430] |
| 3 | test_execute_command_is_supported     | port_list.servers.mask[435] |

**5.3.8. Generic node commands (uavcan.node.ExecuteCommand)**

> not yet, but it is partically tested in other tests

**5.3.9. Node software update**

> not yet

**5.3.10. Register interface**

| № | Name                      | Test case description |
| - | ------------------------- | --------------------- |
| 1 | test_registers_name | Register name should follow the specific pattern. |
| 2 | test_default_registers_existance | 1. uavcan.node.id register must exist </br> 2. uavcan.node.description register must exist |
| 3 | test_port_id_register | Port .id registers (uavcan.PORT_TYPE.PORT_NAME.id) must be natural16[1], mutable, persistent and the default value is 65535 |
| 4 | test_port_type_register | Port .type registers (uavcan.PORT_TYPE.PORT_NAME.type) must be string, immutable and persistent |
| 5 | test_persistent_memory | 1. y r <id> uavcan.node.description <random_string> </br> 2. y cmd <id> 65530 </br> 3. y cmd <id> 65535 </br> 4. y r <id> uavcan.node.description # <random_string> |

**5.3.11. Diagnostics and event logging**

> not yet

**5.3.12. Plug-and-play nodes**

> not yet

**Assumptions**

- there is only one node only online and Node ID != 127
- a few tests are skipped for yakut node

## USAGE

**Installation**

```
pip install pycyphal pytest pytest-asyncio
```

**1. Manual usage**

1. Set environment variables with `source cyphal/setup_linux_slcan.sh`, `source cyphal/init.sh` or any other way you want

2. Run the script
    ```bash
    pytest cyphal/specification_checker.py --verbose
    ```

    A usage example is demonstrated below:

    ![](https://github.com/PonomarevDA/tools/blob/docs/assets/cyphal/specification_checker.gif?raw=true)

**2. Usage with Github Actions**

Check examples with:
- Yakut: https://github.com/PonomarevDA/tools/blob/main/.github/workflows/specification_checker.yml.
- RaccoonLab Mini node: https://github.com/RaccoonlabDev/mini_v2_node/blob/main/.github/workflows/cyphal.yml
