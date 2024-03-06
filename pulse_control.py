import asyncio
import os
from pathlib import Path

from pprint import pprint

import pycyphal
import pycyphal.application
import uavcan.node
import numpy as np

from pycyphal.application import make_transport
from pycyphal.application.register import Natural16, Natural32, ValueProxy

from uavcan.primitive.scalar.Real32_1_0 import Real32_1_0
from voltbro.blheli.thrust_sample_1_0 import thrust_sample_1_0


dir_path = Path(__file__).parent / "data"


class PulseControl:
    def __init__(self, register_file_name="PulseControl.db") -> None:
        self.REGISTER_FILE = dir_path / register_file_name
        node_info = uavcan.node.GetInfo_1.Response(
            software_version=uavcan.node.Version_1(major=1, minor=0),
            name="org.voltbro.pulse_control",
        )
        self._node = pycyphal.application.make_node(
            node_info,
            self.REGISTER_FILE,
            transport=make_transport(
                {
                    "uavcan.can.iface": ValueProxy("socketcan:can0"),
                    "uavcan.node.id": ValueProxy(Natural16([89])),
                    "uavcan.can.mtu": ValueProxy(Natural16([64])),
                    "uavcan.can.bitrate": ValueProxy(Natural32([500000, 4000000])),
                }
            ),
        )
        self._node.heartbeat_publisher.mode = uavcan.node.Mode_1.OPERATIONAL
        self._node.heartbeat_publisher.vendor_specific_status_code = os.getpid() % 100

        self.pulse_sub = self._node.make_subscriber(thrust_sample_1_0, 6586)
        self.pulse_pub = self._node.make_publisher(Real32_1_0, 6585)

        self.pulse = np.nan

        self.pulse_sub.receive_in_background(self.read)

    def read(self, data: thrust_sample_1_0, _):
        pulse, ms = PulseControl.parse_pulse_sample(data)
        self.pulse = pulse

    def write(self, pulse):
        return self.pulse_pub.publish(Real32_1_0(pulse))

    def start(self):
        self._node.start()

    def close(self) -> None:
        self._node.close()

    @staticmethod
    def parse_pulse_sample(sample: thrust_sample_1_0):
        return sample.thrust.value, sample.timestamp.microsecond


async def _main():
    pulse_reader = PulseControl()
    pulse_reader.start()
    try:
        while True:
            pprint(pulse_reader.pulse)
            await asyncio.sleep(0.01)
    except KeyboardInterrupt:
        pulse_reader.close()


if __name__ == "__main__":
    asyncio.run(_main())
