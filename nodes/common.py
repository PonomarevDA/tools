#!/usr/bin/env python3
import os
import yaml
import subprocess
from pathlib import Path
import wget

REPO_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path(__file__).resolve().parent / 'latest_firmware.yml'
FLASH_SCRIPT_PATH = REPO_DIR / 'stm32' / 'flash.sh'
BINARY_DIR = REPO_DIR / 'binaries'
BINARY_PATH = str(BINARY_DIR / 'latest.bin')


def download_firmware(url : str) -> str:
    Path(BINARY_DIR).mkdir(parents=True, exist_ok=True)
    if os.path.exists(BINARY_PATH):
        os.remove(BINARY_PATH)
    filename = wget.download(url, out=BINARY_PATH)
    return filename

def upload_firmware(protocol : str, node : str):
    with open(CONFIG_PATH, 'r') as file:
        firmware = yaml.safe_load(file)[protocol][node]
        if firmware.startswith("https"):
            download_firmware(firmware)
            binary_path = BINARY_PATH
        else:
            binary_path = firmware

        subprocess.Popen(f"{FLASH_SCRIPT_PATH} {binary_path}".split(), stdout=subprocess.PIPE).communicate()
