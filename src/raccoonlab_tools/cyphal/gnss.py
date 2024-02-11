#!/usr/bin/env python3
# This software is distributed under the terms of the MIT License.
# Copyright (c) 2023 Dmitry Ponomarev.
# Author: Dmitry Ponomarev <ponomarevda96@gmail.com>
import asyncio
import datetime
import random
import math

import pycyphal.application
# pylint: disable=import-error
import uavcan.node
import ds015.service.gnss.Gnss_0_1
from raccoonlab_tools.cyphal.utils import RegisterInterface, PortRegisterInterface


class TimeWeekChecker:
    def __init__(self, cyphal_node, dest_node_id):
        self._node = cyphal_node
        self._dest_node_id = dest_node_id
        self._port_interface = PortRegisterInterface(self._node)

    async def run(self):
        reg_name = "uavcan.pub.ds015.gps.gnss.id"
        gnss_port_id = await self._port_interface.get_id(self._dest_node_id, reg_name)
        if gnss_port_id == 65535:
            print(f"GNSS port {reg_name} is disabled. ")
            print(f"Type `y r {self._dest_node_id} {reg_name} <port_id>`")
            return

        sub = self._node.make_subscriber(ds015.service.gnss.Gnss_0_1, gnss_port_id)
        sub.receive_in_background(self._callback)
        await asyncio.sleep(5)

    async def _callback(self, msg, transfer_from):
        if math.isclose(msg.point.latitude, 0.0, abs_tol=1e-05) and \
           math.isclose(msg.num_sats, 0.0, abs_tol=1e-05):
            print(f"GNSS has not been estimate the date yet.")
            return

        timeweek_ms_now = self.get_gnss_timeweek_ms_now()
        time_week_ms_err = timeweek_ms_now - msg.time_week_ms
        print(f"time_week_ms: {msg.time_week_ms} vs {timeweek_ms_now}, err = {time_week_ms_err} ms")

        week_number = self.get_gnss_week_number()
        week_number_err = week_number - msg.time_week
        print(f"week_number: {msg.time_week} vs {week_number}, err = {week_number_err} weeks")

    @staticmethod
    def calculate_gnss_weekday(gnss_ts : datetime.datetime):
        """
        The [Sun-Fri] : [0-6] presents day of week and day of week number
        Reference: https://geodesy.noaa.gov/CORS/resources/gpscals.shtml
        """
        return (gnss_ts.weekday() + 1) % 7

    @staticmethod
    def get_gnss_week_number():
        """
        The Week presents the full GPS week number since the 1st epoch (Jan 06, 1980)
        """
        gnss_first_ts = datetime.datetime(1980, 1, 6, 0, 0) + datetime.timedelta(seconds=19-9)
        gnss_now_ts = datetime.datetime.utcnow() + datetime.timedelta(seconds=27-9)
        elapsed_seconds = int((gnss_now_ts - gnss_first_ts).total_seconds())
        week_number = int(elapsed_seconds / 604800)
        return week_number

    @staticmethod
    def get_gnss_timeweek_ms_now():
        """
        GPS = UTC + LS - 9
        Reference: https://github.com/OpenCyphal/public_regulated_data_types/blob/master/uavcan/time/TAIInfo.0.1.dsdl
        """
        utc_ts = datetime.datetime.utcnow()
        gnss_ts = utc_ts + datetime.timedelta(seconds=27-9)
        weekday = TimeWeekChecker.calculate_gnss_weekday(gnss_ts)
        time_week_sec = gnss_ts.second + 60 * gnss_ts.minute + 60*60 * gnss_ts.hour +  60*60*24 * weekday
        time_week_ms = time_week_sec * 1000 + int(gnss_ts.microsecond / 1000)
        return time_week_ms

def random_integer(excluded_set):
    num = random.randint(0, 6143)
    while num in excluded_set:
        num = random.randint(0, 6143)
    return num

async def main(dest_node_id):
    software_version = uavcan.node.Version_1_0(major=1, minor=0)
    node_info = uavcan.node.GetInfo_1_0.Response(
        software_version,
        name="co.raccoonlab.gnss_checker"
    )
    cyphal_node = pycyphal.application.make_node(node_info)
    cyphal_node.heartbeat_publisher.mode = uavcan.node.Mode_1_0.OPERATIONAL
    cyphal_node.start()

    # await TimeWeekChecker(cyphal_node, dest_node_id).run()

    register_inrerface = RegisterInterface(cyphal_node)
    port_interface = PortRegisterInterface(cyphal_node)

    access_client = cyphal_node.make_client(uavcan.register.Access_1_0, dest_node_id)
    register_names = await register_inrerface.register_list(dest_node_id)
    occupied_port_id = set()
    for reg_name in register_names:
        if not reg_name.startswith("uavcan.") or not reg_name.endswith(".id"):
            continue
        port_id = await port_interface.get_id(dest_node_id, reg_name)
        occupied_port_id.add(port_id)
        if port_id == 65535:
            free_port_id = random_integer(occupied_port_id)
            print(reg_name, port_id, free_port_id)
            set_request = uavcan.register.Access_1_0.Request()
            set_request.name.name = reg_name
            set_request.value.natural16 = uavcan.primitive.array.Natural16_1_0(free_port_id)
            access_response = await access_client.call(set_request)
        # else:
        #     print(reg_name, port_id)

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Cyphal specification checker')
    parser.add_argument("--node", default='50', type=int, help="Destination node identifier")
    args = parser.parse_args()
    asyncio.run(main(dest_node_id=args.node))
