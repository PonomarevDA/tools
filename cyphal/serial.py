#!/usr/bin/env python3
import asyncio
import sys
import pathlib

try:
    compiled_dsdl_dir = pathlib.Path(__file__).resolve().parent.parent / "compile_output"
    sys.path.insert(0, str(compiled_dsdl_dir))
    import pycyphal.application
    import uavcan.node
    import uavcan.metatransport.serial.Fragment_0_2
except (ImportError, AttributeError):
    sys.exit()
REGISTER_FILE = "allocation_table.db"

class CyphalCommunicator:
    def __init__(self):
        self._cyphal_node = None
        self._rx_counter = 0

    async def main(self):
        node_info = uavcan.node.GetInfo_1_0.Response(
            software_version=uavcan.node.Version_1_0(major=1, minor=0),
            name="example_node",
        )
        self._cyphal_node = pycyphal.application.make_node(node_info)
        self._cyphal_node.heartbeat_publisher.mode = uavcan.node.Mode_1_0.OPERATIONAL
        self._cyphal_node.heartbeat_publisher.vendor_specific_status_code = 50
        self._cyphal_node.start()

        self._cyphal_node.registry["uavcan.sub.tunnel.id"] = 3500

        self._sp_sub = self._cyphal_node.make_subscriber(uavcan.metatransport.serial.Fragment_0_2, "tunnel")
        self._sp_sub.receive_in_background(self._sub_cb)

        while True:
            await asyncio.sleep(1)

    async def _sub_cb(self, msg, _, chunk_size=80):
        size = len(msg.data.tobytes())
        for first_index in range(0, size, chunk_size):
            last_index = first_index + min(size - first_index, chunk_size)
            print(f"RX {self._rx_counter : < 5} bytes: {msg.data[first_index : last_index].tobytes()}")
            self._rx_counter += last_index - first_index

if __name__ == "__main__":
    asyncio.run(CyphalCommunicator().main())
