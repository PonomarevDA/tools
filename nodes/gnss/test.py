#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
from pathlib import Path

nodes_dir = Path(__file__).resolve().parent.parent
repo_dir = nodes_dir.parent
sys.path.insert(0, str(nodes_dir))
sys.path.insert(0, str(repo_dir / "cyphal"))
sys.path.insert(0, str(repo_dir / "dronecan"))

from gnss import test_dronecan_gps_mag_baro
from specification_checker import test_cyphal_standard
from common import upload_firmware


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
    parser.add_argument("--hw-version", type=str, required=True, help="[v2, v3]")
    parser.add_argument("--port", default='slcan0', type=str, help="[slcan0, ...]")
    parser.add_argument("--printer", default=False, action='store_true', help="Print report")
    parser.add_argument("--onlytest", default=False, action='store_true', help="Print report")
    args = parser.parse_args()

    REPORT_PATH = "report.txt"

    node_name = f"gnss_v{args.hw_version}"

    if not args.onlytest:
        if args.protocol == 'cyphal':
            upload_firmware(args.protocol, node_name)
        elif args.protocol == 'dronecan':
            upload_firmware(args.protocol, node_name)

    if args.protocol == 'dronecan':
        test_dronecan_gps_mag_baro(args.port, REPORT_PATH)
    elif args.protocol == 'cyphal':
        test_cyphal_standard(50)

    if args.printer:
        print_report(filename=REPORT_PATH)
