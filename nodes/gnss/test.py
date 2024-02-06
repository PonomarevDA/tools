#!/usr/bin/env python3
import sys
from pathlib import Path

from raccoonlab_tools.common.printer import Printer

nodes_dir = Path(__file__).resolve().parent.parent
repo_dir = nodes_dir.parent
sys.path.insert(0, str(nodes_dir))
sys.path.insert(0, str(repo_dir / "cyphal"))
sys.path.insert(0, str(repo_dir / "dronecan"))

from gnss import test_dronecan_gps_mag_baro
from specification_checker import run_cyphal_standard_checker
from common import upload_firmware


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
        run_cyphal_standard_checker(50)

    if args.printer:
        Printer.print(filename=REPORT_PATH)
