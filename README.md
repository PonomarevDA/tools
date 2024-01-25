# Cyphal/DroneCAN nodes tools  [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=PonomarevDA_tools&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=PonomarevDA_tools) [![cyphal_init.sh](https://github.com/PonomarevDA/tools/actions/workflows/cyphal_init.yml/badge.svg)](https://github.com/PonomarevDA/tools/actions/workflows/cyphal_init.yml) [![specification_checker.py](https://github.com/PonomarevDA/tools/actions/workflows/specification_checker.yml/badge.svg)](https://github.com/PonomarevDA/tools/actions/workflows/specification_checker.yml)

`tools` is a collection of bash and python scripts for testing and configuration of Cyphal/CAN and DroneCAN nodes.

It is expected to use Ununtu 20.04 or newer.

## Cyphal/CAN

For details of the Cyphal related scripts please check the corresponded [cyphal/README.md](cyphal/README.md) file. Here is a brief info of the most essential scripts:

1. [cyphal/init.sh](cyphal/init.sh) is used for automatically:
    1. Create CAN-interface either on a real CAN-sniffer or vitual CAN interface
    2. Configure environment variables for Yakut or Yukon
    3. Compile DSDL based on public regulated data types
2. [cyphal/specification_checker.py](cyphal/specification_checker.py) can be used as part of CI or just to check does a not correspond to the Cyphal standard or not. |

## CAN

Cyphal/CAN and DroneCAN scripts are basically based on the [can/create_slcan.sh](can/create_slcan.sh) script: 

```bash
./can/create_slcan.sh --help
```

## STM32 tools

A few STM32 related scripts are located in [stm32](stm32) folder:

1. Update STM32 firmware:

    ```bash
    ./stm32/flash.sh <path_to_the_binary.bin>
    ```

2. Build STM32CubeIDE project with CLI:

    ```bash
    cd repo
    ./tools/stm32/build_cubeide.sh -v -c /opt/stm32cubeide/stm32cubeide -d . -p project_example
    ```

## DroneCAN

> Work in progress...

## RaccoonLab nodes

> Work in progress. A few RaccoonLab nodes related scripts will be located in [nodes](nodes) folder.

## License

The scripts are distributed under MIT license. In general, you can do with them whatever you want. If you find a bug, please suggest a PR or an issue.
