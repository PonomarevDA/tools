#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
"""
XPRINTER XP-365B driver
"""
import os
import subprocess
import logging
import argparse

class Printer:
    @staticmethod
    def print(filename, printer_name="XP-365B"):
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

        cmd = ["lp", "-o", "media=Custom.40x30mm", "-d", printer_name, filename]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        proc.communicate()

if __name__ =="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', help="File to be printed")
    args = parser.parse_args()
    Printer.print(args.file)
