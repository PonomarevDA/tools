#!/usr/bin/env python3
from argparse import ArgumentParser
from common import upload_firmware
import subprocess

SUPPORTED_PROTOCOLS = ["cyphal", "dronecan"]
SUPPORTED_NODES = ["mini", "micro", "kirpi", "gnss_v2", "gnss_v3"]

if __name__ == "__main__":
    parser = ArgumentParser(description='RaccoonLab node tester:'
                                        '1. Download latest firmware and upload it to the target '
                                        '2. Provide tests '
                                        '3. Print result')
    parser.add_argument("--protocol",
                        type=str,
                        required=True,
                        choices=SUPPORTED_PROTOCOLS,
                        help=str(SUPPORTED_PROTOCOLS))
    parser.add_argument("--node",
                        type=str,
                        required=True,
                        choices=SUPPORTED_NODES,
                        help=str(SUPPORTED_NODES))
    parser.add_argument("--upload",
                        action='store_true',
                        help="[False (by default), True]")
    parser.add_argument("--test",
                        action='store_true',
                        help="[False (by default), True]")
    args = parser.parse_args()

    if args.upload:
        upload_firmware(protocol=args.protocol, node=args.node)

    if args.test:
        if args.protocol == 'cyphal':
            subprocess.Popen(f"./cyphal/init.sh".split(), stdout=subprocess.PIPE).communicate()
            import pytest
            retcode = pytest.main(["-x", "cyphal/specification_checker.py"])
    