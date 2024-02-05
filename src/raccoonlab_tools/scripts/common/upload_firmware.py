#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import os
import sys
import subprocess
import argparse as ap
import argcomplete
import yaml
import wget
from raccoonlab_tools.common.st_link_linux import StlinkLinux

DOWNLOAD_BINARY_DIR = '.'
DOWNLOAD_BINARY_PATH = 'latest.bin'


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
        subprocess.run(["gh",
                        "-R",
                        firmware_link,
                        "release",
                        "download",
                        "--pattern",
                        '*.bin',
                        "--dir",
                        DOWNLOAD_BINARY_DIR]
        )
    else:
        print("[ERROR] I don't know.")
        sys.exit(1)

    assert isinstance(binary_path, str)
    return binary_path

def main():
    parser = ap.ArgumentParser()
    parser.add_argument('--config', required=True)
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    config_path = args.config
    with open(config_path, "r", encoding='UTF-8') as stream:
        config = yaml.safe_load(stream)

    binary_path = get_firmware(config['metadata']['link'])
    StlinkLinux.upload_firmware(binary_path)

if __name__ == '__main__':
    main()
