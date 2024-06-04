## CYPHAL SPECIFICATION CHECKER

[specification_checker.py](specification_checker.py) is a collection of pytest tests for a few Application-level functions described in [the Cyphal specification](https://opencyphal.org/specification/Cyphal_Specification.pdf).

All tests are divided into a few groups. A brief their description is shown below.

**5.3.2. Node heartbeat (uavcan.node.Heartbeat)**

| № | Name                   | Test case description |
| - | ---------------------- | --------------------- |
| 1 | test_frequency         | 1. Wait for 5 Heartbeats </br> 2. Check that the publishing rate is exactly 1 Hz |
| 2 | test_uptime            | 1. Wait for 5 Heartbeats </br> 2. Check that the uptime is correctly increased. The node should not be rebooted during the test. </br> This test is useful for Watchdog issues detection. |

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

- there is only one online node and Node ID != 127
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

    <img src="https://github.com/PonomarevDA/tools/wiki/assets/cyphal/specification_checker.gif" alt="drawing"/>

**2. Usage with Github Actions**

Check examples with:
- Yakut: https://github.com/PonomarevDA/tools/blob/main/.github/workflows/specification_checker.yml.
- RaccoonLab Mini node: https://github.com/RaccoonlabDev/mini_v2_node/blob/main/.github/workflows/cyphal.yml
