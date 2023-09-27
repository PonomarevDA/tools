# Cyphal/DroneCAN nodes tools

`tools` is a collection of bash and python scripts for testing and configuration of Cyphal/CAN and DroneCAN nodes.

It is expected to use Ununtu 20.04 or newer.

## Install dependencies

```bash
./install_for_ubuntu.sh
```

## Cyphal usage

The following script automatically:
1. Create SLCAN based on CAN-sniffer
2. Configure environment variables if they are not already configured
3. Compile DSDL based on public regulated data types

```bash
source cyphal/init.sh --help
```

> The script expects you have clonned [public_regulated_data_types](https://github.com/OpenCyphal/public_regulated_data_types) inside this repository. It will compile everything into `build` directory and create interface with name `slcan0`. You can override these parameters by manually setting the following environment variables: `REG_DATA_TYPE_PATH`, `YAKUT_COMPILE_OUTPUT`, `UAVCAN__CAN__IFACE`.

## DroneCAN usage

Create SLCAN:

```bash
./can/create_slcan.sh --help
```

## STM32 usage

Update STM32 firmware:

```bash
./stm32/flash.sh <path_to_the_binary.bin>
```

Build STM32CubeIDE project with CLI:

```bash
cd repo
./tools/stm32/build_cubeide.sh -v -c /opt/stm32cubeide/stm32cubeide -d . -p project_example
```

Generate git hash and software version based on git tag:

```bash
cd <root_of_the_repo>
./stm32/generate_git_hash.sh <output_dir>
```

```bash
cd <root_of_the_repo>
./stm32/generate_software_version.sh <output_dir>
```

## License

The scripts are distributed under MIT license. In general, you can do with them whatever you want. If you find a bug, please suggest a PR or an issue.
