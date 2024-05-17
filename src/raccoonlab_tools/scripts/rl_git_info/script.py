#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
"""
Semantic Versioning v2.0.0 parser https://semver.org/
"""
import subprocess
import argparse
import re

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--major", action='store_true')
    parser.add_argument("--minor", action='store_true')
    parser.add_argument("--patch", action='store_true')
    args = parser.parse_args()

    latest_tag = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], stdout=subprocess.PIPE, text=True).stdout.strip()
    semver = latest_tag[1:]

    pattern = r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    match = re.match(pattern, semver)

    if args.major:
        print(match.group('major'))
    elif args.minor:
        print(match.group('minor'))
    elif args.patch:
        print(match.group('patch'))
    else:
        print("Latest tag:", semver)
        print("Major version:", match.group('major'))
        print("Minor version:", match.group('minor'))
        print("Patch version:", match.group('patch'))

if __name__ == "__main__":
    main()
