#!/usr/bin/env python3
import sys
from pathlib import Path

nodes_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(nodes_dir))

from common import upload_firmware

if __name__ == "__main__":
    upload_firmware("cyphal", "mini")
