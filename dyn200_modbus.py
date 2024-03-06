"""
modbus parser: https://rapidscada.net/modbus/
CRC calculation: https://crccalc.com/
modbus description: https://ozeki.hu/p_5878-mobdbus-function-code-3-read-multiple-holding-registers.html
"""

import serial


class DYN200Reader:
    """
    +-----------------------+---------+--------+

    | Device name           | 1 byte  | 0x01   |

    | Function code         | 1 byte  | 0x03   |

    | Starting Address      | 2 bytes | 0x00   |

    | Quantity of Registers | 2 bytes | 0x06   |

    | CRC                   | 2 bytes | 0xC8C5 |

    +-----------------------+---------+--------+
    """

    COMMAND = b"\x01\x03\x00\x00\x00\x06\xC5\xC8"

    def __init__(self, port="/dev/ttyUSB0", baudrate=57600):
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
        )

    def read_torque(self):
        self.ser.write(DYN200Reader.COMMAND)
        s = self.ser.read(17)

        tor = s[3:7]
        vel = s[7:11]
        pwr = s[11:15]

        tor = int.from_bytes(tor, "big", signed=True) / 100.0
        vel = int.from_bytes(vel, "big", signed=True) / 10.0
        pwr = int.from_bytes(pwr, "big", signed=True) / 1.0

        return tor
