"""
LINE Simple Beacon core functionality
Provide data construction, validation, and error handling
"""

# LINE Simple Beacon constants
FRAME_TYPE = 0x02
HWID_LENGTH = 10  # 10 hexadecimal characters = 5 bytes
MAX_DEVICE_MESSAGE_LENGTH = 13  # 13 bytes
DEFAULT_MEASURED_POWER = 0x7F

# BLE broadcasting data types
ADTYPE_FLAGS = 0x01
ADTYPE_COMPLETE_16_BIT_SERVICE_UUID = 0x03
ADTYPE_SERVICE_DATA = 0x16

# LINE Simple Beacon UUID (little-endian)
UUID16LE_FOR_LINECORP = bytes([0x6f, 0xfe])

class BeaconCore:
    """LINE Simple Beacon core functionality class"""

    @classmethod
    def build_line_simple_beacon_service_data(cls, hwid: str, device_message: str) -> bytes:
        """
        assemble LINE Simple Beacon Service Data
        :param hwid: 10 hex string
        :param device_message: 1~13 bytes hex string
        :return: bytes, content is 0x6f, 0xfe + line_simple_beacon_frame (frame_type + hwid in bytes + measured_tx_power + device_message)
        """

        frame_type = bytes([FRAME_TYPE])
        hwid_bytes = bytes.fromhex(hwid)
        device_message_bytes = bytes.fromhex(device_message)
        measured_tx_power = bytes([DEFAULT_MEASURED_POWER])
        line_simple_beacon_frame = frame_type + hwid_bytes + measured_tx_power + device_message_bytes
        uuid16le = bytes(UUID16LE_FOR_LINECORP)
        return uuid16le + line_simple_beacon_frame