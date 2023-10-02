#!/usr/bin/env python3
import can


def send_one():
    bus = can.Bus(interface='socketcan', channel='slcan0', bitrate=1000000)

    cyphal_node_id = 127
    heartbeat_frame_id = 0x107D55 + cyphal_node_id
    msg = can.Message(arbitration_id=heartbeat_frame_id, data=[0, 25, 0, 1, 3, 1, 4, 1], is_extended_id=True)

    try:
        for _ in range(101):
            bus.send(msg)
        print(f"Message sent on {bus.channel_info}")
    except can.CanError:
        print("Message NOT sent")


if __name__ == "__main__":
    send_one()