"""
LINE Simple Beacon macOS platform implementation
Use CoreBluetooth framework
"""

import objc
from PyObjCTools import AppHelper
from typing import Dict, Any
import time
import binascii
from core.beacon_core import BeaconCore

# Load CoreBluetooth framework
CoreBluetooth = objc.loadBundle(
    'CoreBluetooth',
    globals(),
    bundle_path='/System/Library/Frameworks/CoreBluetooth.framework'
)

# Load needed classes
NSObject = objc.lookUpClass('NSObject')
NSData = objc.lookUpClass('NSData')
CBPeripheralManager = objc.lookUpClass('CBPeripheralManager')
CBUUID = objc.lookUpClass('CBUUID')

# Load Foundation classes
from Foundation import NSMutableDictionary, NSString, NSArray


class MacOSBeaconDelegate(NSObject):
    """CoreBluetooth Peripheral Manager Delegate"""
    
    def initWithTransmitter_(self, transmitter):
        """Initialize delegate
        
        Args:
            transmitter: MacOSTransmitter instance
        """
        self = objc.super(MacOSBeaconDelegate, self).init()
        if self is None:
            return None
        
        self.transmitter = transmitter
        self._init_complete = False
        return self
    
    def peripheralManagerDidUpdateState_(self, peripheral):
        """Callback function when Bluetooth state changes"""
        states = {
            0: "Unknown",
            1: "Resetting",
            2: "Unsupported",
            3: "Unauthorized",
            4: "PoweredOff",
            5: "PoweredOn",
        }
        
        state = peripheral.state()
        state_name = states.get(state, "Unknown")
        print(f"Bluetooth state: {state_name}")
        
        if state == 5:  # CBPeripheralManagerStatePoweredOn
            self.transmitter._set_initialized_state(True)
            self._init_complete = True
            # Stop event loop after getting PoweredOn state.
            AppHelper.stopEventLoop()
        else:
            self.transmitter._set_initialized_state(False)
            self.transmitter._set_advertising_state(False)
            self._init_complete = True
    
    def peripheralManagerDidStartAdvertising_error_(self, peripheral, error):
        """Callback function when broadcasting starts"""
        if error:
            print(f"DEBUG: Broadcasting failed, error: {error}")
            self.transmitter._set_advertising_state(False)
        else:
            print("DEBUG: Broadcasting started successfully")
            self.transmitter._set_advertising_state(True)
        # Stop event loop after broadcasting starts. Important!
        AppHelper.stopEventLoop()

class MacOSTransmitter():
    """macOS platform transmitter implementation"""
    
    def __init__(self):
        """Initialize macOS transmitter"""
        super().__init__()
        self._peripheral_manager = None
        self._delegate = None
        self._should_stop = False
        self._is_initialized = False
        self._is_advertising = False    

    def _set_initialized_state(self, state: bool) -> None:
        self._is_initialized = state

    def _set_advertising_state(self, state: bool) -> None:
        self._is_advertising = state

    def _run_event_loop(self, timeout):
        """Execute event loop, and set timeout
        
        Args:
            timeout: timeout in seconds
        """
        print(f"DEBUG: Execute event loop {timeout} seconds")
        try:
            AppHelper.runConsoleEventLoop(timeout)
            print("DEBUG: Event loop period completed")
        except KeyboardInterrupt:
            print("DEBUG: Event loop interrupted (KeyboardInterrupt)")
            self._should_stop = True
            AppHelper.stopEventLoop()
        except Exception as e:
            print(f"DEBUG: Event loop exception: {e}")
    
    def initialize(self) -> bool:
        """Initialize CoreBluetooth
        
        Returns:
            bool: If initialization is successful, return True
        """
        print("DEBUG: Entering initialize()")
        self._delegate = MacOSBeaconDelegate.alloc().initWithTransmitter_(self)
        self._peripheral_manager = CBPeripheralManager.alloc().initWithDelegate_queue_options_(
            self._delegate, None, None
        )
        print("DEBUG: Created delegate and peripheral_manager")
        print("DEBUG: Waiting for Bluetooth state update... (Press Ctrl+C to end)")
        try:
            AppHelper.runConsoleEventLoop()  # Start event loop.
        except KeyboardInterrupt:
            print("DEBUG: KeyboardInterrupt, stop event loop")
            AppHelper.stopEventLoop() # Ensure stop event loop when Ctrl+C is pressed
        
        if self._is_initialized:
            print("DEBUG: Initialization successful.")
            return True
        else:
            print("DEBUG: Initialization failed.")
            return False
    
    def start_advertising(self, hwid: str, device_message: str) -> bool:
        """
        Start broadcasting LINE Simple Beacon (macOS specific)
        Args:
            hwid: Hardware ID (10-digit hexadecimal string)
            device_message: Device message (16-digit hexadecimal string)
        Returns:
            bool: If broadcasting starts successfully, return True
        """
        print("==== DEBUG: Calling start_advertising ====")
        if not self._is_initialized:
            print("DEBUG: Not initialized!")
            raise Exception("Not initialized")

        print(f"DEBUG: Bluetooth state: {self._peripheral_manager.state()}")
        if self._peripheral_manager.state() != 5:
            raise Exception("Bluetooth not powered on")

        try:
            print("DEBUG: Building LINE Simple Beacon Service Data")
            service_data_bytes = BeaconCore.build_line_simple_beacon_service_data(hwid, device_message)
            print(f"DEBUG: Service Data (hex)：{binascii.hexlify(service_data_bytes).decode()}")

            # Assemble CoreBluetooth broadcast data
            line_service_uuid_str = "FE6F"
            beacon_nsdata = NSData.dataWithBytes_length_(service_data_bytes, len(service_data_bytes))

            adv_data = NSMutableDictionary.dictionary()
            service_uuids_key = NSString.stringWithString_("CBAdvertisementDataServiceUUIDsKey")
            service_data_key = NSString.stringWithString_("CBAdvertisementDataServiceDataKey")

            # Use NSString string directly, don't use CBUUID
            adv_data.setObject_forKey_([NSString.stringWithString_(line_service_uuid_str)], service_uuids_key)
            service_data_dict = NSMutableDictionary.dictionary()
            service_data_dict.setObject_forKey_(beacon_nsdata, NSString.stringWithString_(line_service_uuid_str))
            adv_data.setObject_forKey_(service_data_dict, service_data_key)

            print(f"DEBUG: Broadcast data: {adv_data}")

            print("DEBUG: Calling startAdvertising_")
            self._peripheral_manager.startAdvertising_(adv_data)
            print("DEBUG: Called startAdvertising_, waiting for callback")

            # Use timeout and check _is_advertising in the delegate.
            timeout = 10
            start_time = time.time()
            while not self._is_advertising and time.time() - start_time < timeout:
                self._run_event_loop(0.1)  # Short timeout, to keep the loop responsive.

            if self._is_advertising:
                print("DEBUG: Broadcasting started successfully!")
                return True
            else:
                self._peripheral_manager.stopAdvertising()
                print("DEBUG: Broadcasting did not start after timeout.")
                return False

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"DEBUG ERROR: {e}\n{error_details}")
            raise Exception(f"Broadcasting failed: {e}")
    
    def stop_advertising(self) -> bool:
        """Stop broadcasting
        
        Returns:
            bool: If stopping is successful, return True
        """
        if not self._is_advertising:
            return True
        
        try:
            self._peripheral_manager.stopAdvertising()
            self._set_advertising_state(False)
            print("DEBUG: Broadcasting stopped.")
            return True
            
        except Exception as e:
            print(f"DEBUG ERROR: Error stopping broadcasting: {e}")
            raise Exception(f"Stopping failed: {e}")
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information
        
        Returns:
            Dict[str, Any]: Platform information
        """
        return {
            "platform": "macOS",
            "bluetooth_state": self._peripheral_manager.state() if self._peripheral_manager else None,
            "is_advertising": self._is_advertising,
            "is_initialized": self._is_initialized
        }
    
    def cleanup(self) -> None:
        """Clean up resources"""
        if self._is_advertising:
            self.stop_advertising()
        
        self._peripheral_manager = None
        self._delegate = None
        self._set_initialized_state(False)
        self._set_advertising_state(False)
        print("DEBUG: Resources cleaned up.")
