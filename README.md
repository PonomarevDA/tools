# Cyphal/DroneCAN nodes tools

`tools` is a collection of bash and python scripts for testing and configuration of Cyphal/CAN and DroneCAN nodes.

It is expected to use Ununtu 20.04 or newer.

> This repository is work in progress. If you find a bug or something is not clear, please open an issue.

The scripts are divided into the following folders:

## Cyphal/CAN

A few Cyphal related scripts are collected here:

1. [cyphal/init.sh](cyphal/init.sh) is used for automatically:
    1. Create CAN-interface either on a real CAN-sniffer or vitual CAN interface
    2. Configure environment variables for Yakut or Yukon
    3. Compile DSDL based on public regulated data types
2. [cyphal/specification_checker.py](cyphal/specification_checker.py) can be used as part of CI or just to check does a not correspond to the Cyphal standard or not. |

For details please check the corresponded [cyphal/README.md](cyphal/README.md) file.

## DroneCAN

> Work in progress...

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

## RaccoonLab nodes

> Work in progress. A few RaccoonLab nodes related scripts will be located in [nodes](nodes) folder.

## License

The scripts are distributed under MIT license. In general, you can do with them whatever you want. If you find a bug, please suggest a PR or an issue.
