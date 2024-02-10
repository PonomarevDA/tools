#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
"""
Suitable for XPRINTER XP-365B
"""
import os
import subprocess
import logging

class Printer:
    @staticmethod
    def print(filename, printer_name="Xerox_Xprinter_XP-365B"):
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
