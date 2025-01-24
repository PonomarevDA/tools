#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import subprocess
import platform
import os
import sys
import wget

DOWNLOAD_BINARY_DIR = '.'
DOWNLOAD_BINARY_PATH = 'latest.bin'


class FirmwareManager:
    @staticmethod
    def upload_firmware(binary_path):
        if not os.path.exists(binary_path):
            print(f"[ERROR] The binary file is not exist: {binary_path}.")
            return

        system = platform.system()
        if system == "Windows":
            ProgrammerWindows.upload_firmware(binary_path)
        elif system == "Linux":
            if (os.path.exists("/proc/device-tree/model")):
                OpenocdLinux.upload_firmware(binary_path)
            else:
                StlinkLinux.upload_firmware(binary_path)
        elif system == "Darwin":
            print("MacOS is not supported yet.")
        else:
            print("Unknown operating system.")

    @staticmethod
    def get_firmware(firmware_link : str):
        """
        Given a link of any type (URL, local binary, github repo), download a binary.
        """
        assert isinstance(firmware_link, str)
        def is_https(string):
            return string.startswith("https://")
        def is_local_binary(string):
            return string.endswith(".bin")
        def is_gh_repo(string):
            parts = string.split('/')
            return len(parts) == 2 and all(parts)

        binary_path = None
        if is_https(firmware_link):
            print(f"[INFO] url {firmware_link}")
            if os.path.exists(DOWNLOAD_BINARY_PATH):
                os.remove(DOWNLOAD_BINARY_PATH)
            binary_path = wget.download(firmware_link, out=DOWNLOAD_BINARY_PATH)
        elif is_local_binary(firmware_link):
            print(f"[INFO] local path {firmware_link}")
            binary_path = firmware_link
        elif is_gh_repo(firmware_link):
            print(f"[INFO] github repository {firmware_link}")
            cmd = ["gh", "-R", firmware_link, "release", "download",
                "--pattern", '*.bin',
                "--dir", DOWNLOAD_BINARY_DIR]
            subprocess.run(cmd, check=False)
        else:
            print("[ERROR] I don't know.")
            sys.exit(1)

        assert isinstance(binary_path, str)
        return binary_path


class StlinkLinux:
    @staticmethod
    def upload_firmware(binary_path):
        """
        st-info --probe returns:
        - b'Found 0 stlink programmers' if programmer is not online
        - b'dev-type:   unknown' if target is not detected
        - b'F1xx Medium-density' or 'STM32F1xx_MD' if stm32f103 is detected
        """
        res = StlinkLinux._st_info()
        if b'Found 0 stlink programmers' in res:
            print("[ERROR] Programmer has not been detected.")
            return
        if b'Found 1 stlink programmer' in res:
            print("[INFO] Found 1 stlink programmer.")

        if b'dev-type:   unknown' in res:
            print("[ERROR] Target device has not been found.")
            return

        print(f"upload {binary_path}")
        if b'F1xx Medium-density' in res or b'STM32F1xx_MD' in res:
            print("[INFO] stm32f103 has been found.")
            cmd = ['st-flash', '--flash=0x00020000', "--reset", "write", binary_path, "0x8000000"]
        else:
            print("[INFO] Target has been found.")
            cmd = ['st-flash', "--reset", "write", binary_path, "0x8000000"]

        subprocess_with_print(cmd)

    @staticmethod
    def _st_info() -> str:
        return subprocess.Popen(["st-info", "--probe"], stdout=subprocess.PIPE).communicate()[0]

class ProgrammerWindows:
    ENV_VAR_NAME = 'STM32_PROGRAMMER_CLI'
    DEFAULT_PATH = ["C:\\Program Files",
                    "STMicroelectronics",
                    "STM32Cube",
                    "STM32CubeProgrammer",
                    "bin",
                    "STM32_Programmer_CLI.exe"
    ]
    DEFAULT_PATH = os.path.join(*DEFAULT_PATH)
    @staticmethod
    def upload_firmware(binary_path : str):
        stm32_programmer_cli_path = os.environ.get(ProgrammerWindows.ENV_VAR_NAME)
        if stm32_programmer_cli_path is None:
            stm32_programmer_cli_path = ProgrammerWindows.DEFAULT_PATH
            print((f"[WARN] The `{ProgrammerWindows.ENV_VAR_NAME}` env is not specified. "
                   f"Use the default path: {ProgrammerWindows.DEFAULT_PATH}."))

        if not os.path.exists(stm32_programmer_cli_path):
            print(f"[ERROR] The cli has not been found here: {stm32_programmer_cli_path}.")
            return

        cmd = [stm32_programmer_cli_path, "-c", "port=SWD", "-w", binary_path, "0x08000000", "-rst"]
        subprocess_with_print(cmd)


def subprocess_with_print(cmd):
    """Origin: https://stackoverflow.com/a/4417735"""
    def execute(cmd):
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True) as popen:
            for stdout_line in iter(popen.stdout.readline, ""):
                yield stdout_line
            popen.stdout.close()
            return_code = popen.wait()
            if return_code:
                raise subprocess.CalledProcessError(return_code, cmd)

    for path in execute(cmd):
        print(path, end="")

class OpenocdLinux:
    @staticmethod
    def upload_firmware(binary_path : str):
        interface = "stlink"
        if (os.path.exists("/proc/device-tree/model")):
            rpi_model = os.popen('cat /proc/device-tree/model').read()
            print(rpi_model)
            if "Raspberry Pi 5" in rpi_model:
                interface = "raspberrypi5-gpiod"
            if "Raspberry Pi 4" in rpi_model:
                interface = "raspberrypi4-native"
            elif "Raspberry Pi 2" in rpi_model:
                interface="raspberrypi2-native"
            elif "Raspberry Pi 3" in rpi_model:
                print("Raspberry Pi 3 is not supported yet")
                return
            else:
                print("Unknown RaspberryPi model")
                interface = "raspberrypi-native"
        print(f"Using {interface} interface")

        target = OpenocdLinux.get_target(interface)
        cmd = ["openocd", "-c", f'source [find interface/{interface}.cfg];\
                                    set CHIPNAME {target};\
                                    source [find target/{target}.cfg];\
                                    program {binary_path} verify reset exit;']
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        _, stdout = process.communicate()
        print(stdout.decode())

    @staticmethod
    def get_target(interface : str):
        cmd = ["openocd", "-c", f"source [find interface/{interface}.cfg];\
                        swd newdap chip cpu -enable; dap create chip.dap -chain-position chip.cpu;\
                        target create chip.cpu cortex_m -dap chip.dap;\
                        init;\
                        dap info;\
                        exit;\
                        shutdown"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        _, stdout = process.communicate()

        lines = stdout.decode()
        if "Cortex-M3" in lines:
            print("Detected: stm32f1x")
            return "stm32f1x"
        elif "Cortex-M0+" in lines:
            print("Detected: stm32g0x")
            return "stm32g0x"
        else:
            print("Unknown target")
            raise RuntimeError("Unknown target")

# Just for test purposes
if __name__ == '__main__':
    print(FirmwareManager.upload_firmware("firmware.bin"))
