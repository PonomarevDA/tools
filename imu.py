#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023-2024 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
"""
pip install pydronecan python-can setuptools
"""

import re
import sys
import time
import statistics
import dronecan
import matplotlib.pyplot as plt

INTERFACE_NAME = sys.argv[1]
# INTERFACE_NAME = "slcan:/dev/ttyACM2"

node = dronecan.make_node(INTERFACE_NAME, node_id=100, bitrate=1000000, baudrate=1000000)

# Global state
imu_timestamps = []

# Callback for AHRS RawIMU messages
def imu_callback(msg):
    imu_timestamps.append(time.time())

# Subscribe to RawIMU
node.add_handler(dronecan.uavcan.equipment.ahrs.RawIMU, imu_callback)

def compute_and_print_stats():
    now = time.time()
    recent = [t for t in imu_timestamps if now - t <= 1.0]
    count = len(recent)

    if count < 2:
        print(f"[{time.strftime('%H:%M:%S')}] No sufficient messages for statistics.")
        return

    delays = [t2 - t1 for t1, t2 in zip(recent, recent[1:])]
    max_delay = max(delays)
    min_delay = min(delays)
    mean_delay = statistics.mean(delays)

    max_ms = max_delay * 1000
    min_ms = min_delay * 1000
    mean_ms = mean_delay * 1000

    max_hz = 1.0 / max_delay if max_delay > 0 else float('inf')
    min_hz = 1.0 / min_delay if min_delay > 0 else float('inf')
    mean_hz = 1.0 / mean_delay if mean_delay > 0 else float('inf')

    print(f"[{time.strftime('%H:%M:%S')}] Mean: {mean_ms:.1f} ms ({mean_hz:.0f} Hz) | "
          f"Max: {max_ms:.1f} ms ({max_hz:.0f} Hz) | "
          f"Min: {min_ms:.1f} ms ({min_hz:.0f} Hz) | "
          f"Count: {count}")

def plot_delays():
    if len(imu_timestamps) < 2:
        print("Not enough data to plot.")
        return

    times = imu_timestamps
    deltas = [t2 - t1 for t1, t2 in zip(times, times[1:])]
    times_rel = [t - times[0] for t in times[1:]]  # Time axis starting from zero
    deltas_ms = [d * 1000 for d in deltas]

    plt.figure(figsize=(10, 5))
    plt.plot(times_rel, deltas_ms, marker='o', linestyle='-')
    plt.title("IMU Message Delays")
    plt.xlabel("Time (s)")
    plt.ylabel("Delay between messages (ms)")
    plt.grid(True)
    plt.tight_layout()
    safe_name = re.sub(r'[\\/:"*?<>|]+', '_', INTERFACE_NAME)
    plt.savefig(f"imu_delays_{safe_name}.png")
    print("Saved delay plot as imu_delays.png")

# Main loop
next_report_time = time.time() + 1

try:
    while True:
        node.spin(0.01)
        now = time.time()
        if now >= next_report_time:
            compute_and_print_stats()
            next_report_time += 1
except KeyboardInterrupt:
    print("Interrupted by user. Plotting delays...")
    plot_delays()
