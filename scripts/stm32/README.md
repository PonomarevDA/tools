# stm32 tools

## Build Stm32CubeIDE cli

The `build_cubeide.sh` script allows to build Stm32CubeIDE project with cli.
It is useful to use the script as part of a CI, for example within Github Actions.

Usage example:

```bash
cd stm32cubeide_project
./build_cubeide.sh -v -c /opt/stm32cubeide/stm32cubeide -d . -p <project_name>
```

Hint how to use within Github Actions:

```bash
wget https://raw.githubusercontent.com/PonomarevDA/tools/main/stm32/build_cubeide.sh
chmod +x build_cubeide.sh
./build_cubeide.sh -v -c /opt/stm32cubeide/stm32cubeide -d . -p ${{ matrix.project_name }}
```

## Flash firmware

```bash
./stm32/flash.sh firmware.bin
```
