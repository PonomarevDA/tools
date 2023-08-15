# stm32 tools

## Build Stm32CubeIDE cli

The `build_cubeide.sh` script allows to build Stm32CubeIDE project with cli.

Usage example:

```bash
cd stm32cubeide_project
./build_cubeide.sh -v -c /opt/stm32cubeide/stm32cubeide -d . -p <project_name>
```

## Flash firmware

```bash
./stm32/flash.sh firmware.bin
```
