"""
LINE Simple Beacon Linux platform implementation
Using hcitool command.
"""

import subprocess
import time
from core.beacon_core import BeaconCore

class LinuxTransmitter():
    def __init__(self):
        self.hcitool_process = None

    def initialize(self):
        """Initialize the BLE adapter"""
        try:
            # Make sure the Bluetooth adapter is up
            subprocess.run(['sudo', 'hciconfig', 'hci0', 'up'], check=True)
            # Stop any existing broadcasts
            subprocess.run(['sudo', 'hciconfig', 'hci0', 'noleadv'], check=False)
            return True
        except Exception as e:
            print(f"Error initializing BLE: {e}")
            return False

    def create_line_simple_beacon_pdu(self, hwid: str, device_message: str = '') -> bytes:
        """Create LINE Simple Beacon advertising PDU"""
        # Get service data from BeaconCore
        service_data = BeaconCore.build_line_simple_beacon_service_data(hwid, device_message)
        
        # Create the advertising data
        # Flags (0x02): LE General Discoverable Mode
        flags = bytes([0x02, 0x01, 0x06])
        
        # LINE Simple Beacon Service UUID (0xFE6F)
        service_uuid = bytes([0x03, 0x02, 0x6F, 0xFE])
        
        # Combine all data
        return flags + service_uuid + service_data

    def start_advertising(self, hwid: str, device_message: str = '') -> bool:
        """Start advertising LINE Simple Beacon signal"""
        try:
            self.stop_advertising()

            # 1. Flags
            flags = bytes([0x02, 0x01, 0x06])
            # 2. Complete List of 16-bit Service UUIDs
            uuid = bytes([0x03, 0x02, 0x6F, 0xFE])
            # 3. Service Data (from BeaconCore)
            service_data = BeaconCore.build_line_simple_beacon_service_data(hwid, device_message)
            # 3.1. Service Data AD structure: [len][0x16][UUID][payload]
            # len = 1 (type) + 2 (uuid) + payload
            service_data_ad = bytes([len(service_data)+1, 0x16]) + service_data

            # Combine complete broadcast data
            adv_data = flags + uuid + service_data_ad

            # Pad to 31 bytes
            if len(adv_data) < 31:
                adv_data += bytes([0x00] * (31 - len(adv_data)))
            elif len(adv_data) > 31:
                print("Warning: Advertising data too long, truncated to 31 bytes")
                adv_data = adv_data[:31]

            # Convert to hcitool cmd format
            hex_data = ' '.join(f'{b:02x}' for b in adv_data)
            cmd = f"sudo hcitool -i hci0 cmd 0x08 0x0008 1f {hex_data}"

            # Set broadcast data
            subprocess.run(cmd, shell=True, check=True)

            # Enable broadcasting
            subprocess.run(['sudo', 'hciconfig', 'hci0', 'leadv'], check=True)

            return True
        except Exception as e:
            print(f"Error starting advertising: {e}")
            return False

    def stop_advertising(self):
        """Stop advertising"""
        try:
            # Stop broadcasting
            subprocess.run(['sudo', 'hciconfig', 'hci0', 'noleadv'], check=False)
            
            # Reset the Bluetooth adapter
            subprocess.run(['sudo', 'hciconfig', 'hci0', 'reset'], check=False)
            
        except Exception as e:
            print(f"Error stopping advertising: {e}")

