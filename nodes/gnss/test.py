#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
from pathlib import Path
import wget

repo_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_dir / "cyphal"))
sys.path.insert(0, str(repo_dir / "dronecan"))

from gnss import test_dronecan_gps_mag_baro
from specification_checker import test_cyphal_standard

RELEASE_URL = "https://github.com/RaccoonlabDev/docs/releases"
URLS = {
    "gnss_v3_cyphal" : f"{RELEASE_URL}/download/v1.5.4/gnss_v3_cyphal_v1.5.4_cb62980.bin",
    "gnss_v2.5_dronecan" : f"{RELEASE_URL}/download/v0.12.2/gnss_v2.5_dronecan_v0.12.1_e0ba916.bin"
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
        firmware = "gnss_v3_cyphal"
    elif protocol == 'dronecan':
        firmware = "gnss_v2.5_dronecan"
    else:
        print("Unknown specified protocol.")
        return

    download_firmware(URLS[firmware])
    upload_firmware(BINARY_PATH)
    print("")

def print_report(filename, printer_name="Xerox_Xprinter_XP-365B"):
    if not os.path.isfile(filename):
        logging.error("File %s is not exist", filename)
        return

    res = subprocess.check_output(["lpstat", "-p", printer_name]).decode()

    if printer_name not in res:
        logging.error("Printer %s is not configured.", printer_name)
        return

    if 'Unplugged or turned off' in res:
        logging.error('Printer is unplugged or turned off')
        return

    proc = subprocess.Popen(f"lp -d {printer_name} {filename}".split(), stdout=subprocess.PIPE)
    proc.communicate()

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Node tester: '
                                        '1. Download latest firmware and upload it to the target '
                                        '2. Provide tests '
                                        '3. Print result')
    parser.add_argument("--protocol", type=str, required=True, help="[cyphal, dronecan]")
    parser.add_argument("--port", default='slcan0', type=str, help="[slcan0, ...]")
    parser.add_argument("--printer", default=False, action='store_true', help="Print report")
    parser.add_argument("--onlytest", default=False, action='store_true', help="Print report")
    args = parser.parse_args()

    REPORT_PATH = "report.txt"

    if not args.onlytest:
        download_firmware_and_upload_to_target(args.protocol)

    if args.protocol == 'dronecan':
        test_dronecan_gps_mag_baro(args.port, REPORT_PATH)
    elif args.protocol == 'cyphal':
        test_cyphal_standard(50)

    if args.printer:
        print_report(filename=REPORT_PATH)
