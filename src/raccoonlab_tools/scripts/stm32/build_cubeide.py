#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>

import os
import subprocess
import argparse

DEFAULT_WORKSPACE_PATH = "~/STM32CubeIDE/workspace_1.5.1"
DEFAULT_STM32_CUBEIDE_PATH = "/opt/stm32cubeide/stm32cubeide"

BUILD_ARGS = (
    "--launcher.suppressErrors "
    "-nosplash "
    "-application org.eclipse.cdt.managedbuilder.core.headlessbuild"
)

def cubeide_build(args):
    cmd = (
        f"{args.cube_ide_path} {BUILD_ARGS} "
        f"-import {args.project_path} "
        f"-build {args.project_name} "
        f"-data {args.workspace_path}"
    )

    if args.suppress_build_logs:
        result = subprocess.run(cmd, shell=True, capture_output=True)
        for line in result.stdout.splitlines():
            if b"Opening" in line or b"Build of configuration" in line or b"Build Finished" in line:
                print(line.decode())
    else:
        subprocess.run(cmd, shell=True)

def main():
    parser = argparse.ArgumentParser(description="STM32CubeIDE build utility")
    parser.add_argument("-v", "--verbose", action="store_true", help="Activate verbose mode")
    parser.add_argument("-s", "--suppress_build_logs", action="store_true", help="Suppress build process logs, show only build result")
    parser.add_argument("-w", "--workspace_path", type=str, default=DEFAULT_WORKSPACE_PATH, help="Specify workspace path")
    parser.add_argument("-c", "--cube_ide_path", type=str, default=DEFAULT_STM32_CUBEIDE_PATH, help="Specify STM32CubeIDE path")
    parser.add_argument("-p", "--project_name", type=str, required=True, help="Specify project name")
    parser.add_argument("--project_path", type=str, default=".", help="Specify project path")
    args = parser.parse_args()

    # Check args
    if not os.path.isfile(args.cube_ide_path):
        print(f"ERROR: CUBE_IDE_PATH={args.cube_ide_path} does not exist!\n"
              "Examples of the path:\n"
              f"- {DEFAULT_STM32_CUBEIDE_PATH}\n"
              "- /opt/st/stm32cubeide_1.5.1/stm32cubeide"
        )
        exit(1)

    if not os.path.isdir(args.workspace_path):
        print(f"WARN: WS_PATH={args.workspace_path} does not exist!")
        print(f"ERROR: CUBE_IDE_PATH={args.cube_ide_path} does not exist!\n"
              "Examples of the path:\n"
              f"- {DEFAULT_WORKSPACE_PATH}\n"
        )
    
    if not os.path.isdir(args.project_path):
        print(f"ERROR: PROJECT_PATH={args.project_path} does not exist!")
        exit(1)

    if args.verbose:
        print("Config:\n"
              f"- Workspace path: {args.workspace_path}\n"
              f"- Stm32CubeIDE path: {args.cube_ide_path}\n"
              f"- Project name: {args.project_name}\n"
              f"- Project path: {args.project_path}", flush=True
        )

    # Build
    os.chdir(args.project_path)
    cubeide_build(args)

if __name__ == "__main__":
    main()
