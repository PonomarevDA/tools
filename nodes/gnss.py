#!/usr/bin/env python3
import os
import wget
import subprocess
from pathlib import Path

URLS = {
    "gnss_v3_cyphal_v1.5.2" : "https://github.com/RaccoonlabDev/docs/releases/download/v1.5.2/gnss_v3_cyphal_v1.5.2_c900ac3.bin",
    "gnss_v2.5_dronecan_v0.12.1" : "https://github.com/RaccoonlabDev/docs/releases/download/v0.12.2/gnss_v2.5_dronecan_v0.12.1_e0ba916.bin"
}
BINARY_FOLDER = 'binaries'
BINARY_PATH = 'binaries/latest.bin'
FLASH_SCRIPT = './stm32/flash.sh'

def download_firmware(url):
    Path(BINARY_FOLDER).mkdir(parents=True, exist_ok=True)
    if os.path.exists(BINARY_PATH):
        os.remove(BINARY_PATH)
    filename = wget.download(url, out=BINARY_PATH)
    return filename

def upload_firmware(binary_path):
    subprocess.Popen(f"{FLASH_SCRIPT} {binary_path}".split(), stdout=subprocess.PIPE).communicate()

def download_firmware_and_upload_to_target(protocol):
    if protocol == 'cyphal':
        firmware = "gnss_v3_cyphal_v1.5.2"
    elif protocol == 'dronecan':
        firmware = "gnss_v2.5_dronecan_v0.12.1"
    else:
        print("Protocol should be specified.")
        return

    download_firmware(URLS[firmware])
    upload_firmware(BINARY_PATH)

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Node firmware uploader')
    parser.add_argument("--protocol", type=str, help="[cyphal, dronecan]")
    args = parser.parse_args()
    download_firmware_and_upload_to_target(args.protocol)
