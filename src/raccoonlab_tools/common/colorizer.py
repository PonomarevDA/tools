#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Colorizer:
    @staticmethod
    def normal(origin_string):
        return origin_string

    @staticmethod
    def header(origin_string):
        """Purple"""
        return f"{Colors.HEADER}{origin_string}{Colors.ENDC}"

    @staticmethod
    def warning(origin_string):
        "Orange"
        return f"{Colors.WARNING}{origin_string}{Colors.ENDC}"

    @staticmethod
    def okcyan(origin_string):
        return f"{Colors.OKCYAN}{origin_string}{Colors.ENDC}"

    @staticmethod
    def okgreen(origin_string):
        return f"{Colors.OKGREEN}{origin_string}{Colors.ENDC}"


    @staticmethod
    def health_to_string(value : int) -> str:
        assert isinstance(value, int)
        mapping = {
            0 : "NOMINAL (0)",
            1 : f"{Colors.HEADER}ADVISORY (1){Colors.ENDC}",
            2 : f"{Colors.WARNING}CAUTION (2){Colors.ENDC}",
            3 : f"{Colors.FAIL}WARNING (3){Colors.ENDC}",
        }
        assert value in mapping
        return mapping[value]

    @staticmethod
    def mode_to_string(value : int) -> str:
        assert isinstance(value, int)
        mapping = {
            0: "OPERATIONAL",
            1: Colorizer.okcyan("INITIALIZATION"),
            2: Colorizer.header("MAINTENANCE"),
            3: Colorizer.warning("SOFTWARE_UPDATE"),
        }

        return mapping[value]