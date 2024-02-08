#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.

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

        cmd = [stm32_programmer_cli_path, "-c", "port=SWD", "-w", binary_path, "0x08000000"]
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


# Just for test purposes
if __name__ == '__main__':
    print(FirmwareManager.upload_firmware("firmware.bin"))
