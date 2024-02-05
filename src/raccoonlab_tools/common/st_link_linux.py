#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.

import subprocess

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


def subprocess_with_print(cmd):
    """Origin: https://stackoverflow.com/a/4417735"""
    def execute(cmd):
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line
        popen.stdout.close()
        return_code = popen.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)

    for path in execute(cmd):
        print(path, end="")


if __name__ == '__main__':
    pass
