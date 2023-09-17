#!/usr/bin/env python3
import asyncio
import sys
import pathlib
import datetime

# pylint: disable-next=wrong-import-position
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "build/nunavut_out"))
import pycyphal.application
# pylint: disable=import-error
import uavcan.node
import ds015.service.gnss.Gnss_0_1


class TimeWeekChecker:
    def __init__(self, cyphal_node, dest_node_id, gnss_port_id):
        self._node = cyphal_node
        self._dest_node_id = dest_node_id
        self._gnss_port_id = gnss_port_id

    async def run(self):
        sub = self._node.make_subscriber(ds015.service.gnss.Gnss_0_1, self._gnss_port_id)
        sub.receive_in_background(self._callback)
        await asyncio.sleep(60*60*24)

    async def _callback(self, msg, transfer_from):
        if msg.point.latitude == 0.0 and msg.num_sats == 0:
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


async def main(dest_node_id):
    software_version = uavcan.node.Version_1_0(major=1, minor=0)
    node_info = uavcan.node.GetInfo_1_0.Response(
        software_version,
        name="co.raccoonlab.gnss_checker"
    )
    cyphal_node = pycyphal.application.make_node(node_info)
    cyphal_node.heartbeat_publisher.mode = uavcan.node.Mode_1_0.OPERATIONAL
    cyphal_node.start()

    await TimeWeekChecker(cyphal_node, dest_node_id, 2201).run()


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Cyphal specification checker')
    parser.add_argument("--node", default='50', type=int, help="Destination node identifier")
    args = parser.parse_args()
    asyncio.run(main(dest_node_id=args.node))
