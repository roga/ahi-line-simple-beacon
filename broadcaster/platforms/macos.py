"""
LINE Simple Beacon macOS platform implementation
Using CoreBluetooth framework, NOT WORK FOR NOW.
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

# Load required classes
NSObject = objc.lookUpClass('NSObject')
NSData = objc.lookUpClass('NSData')
CBPeripheralManager = objc.lookUpClass('CBPeripheralManager')
CBUUID = objc.lookUpClass('CBUUID')

# Load Foundation classes
from Foundation import NSMutableDictionary, NSString

# Define CoreBluetooth constants
kCBAdvDataServiceUUIDs = NSString.stringWithString_("kCBAdvDataServiceUUIDs")
kCBAdvDataServiceData = NSString.stringWithString_("kCBAdvDataServiceData")

class MacOSBeaconDelegate(NSObject):
    """CoreBluetooth peripheral manager delegate"""
    
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
        """Callback when Bluetooth state changes"""
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
        else:
            self.transmitter._set_initialized_state(False)
            self.transmitter._set_advertising_state(False)
            self._init_complete = True
    
    def peripheralManagerDidStartAdvertising_error_(self, peripheral, error):
        """Callback when advertising starts"""
        if error:
            print(f"DEBUG: Advertising failed with error: {error}")
            self.transmitter._set_advertising_state(False)
        else:
            print("DEBUG: Advertising started successfully")
            self.transmitter._set_advertising_state(True)

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
        """Run event loop with timeout
        
        Args:
            timeout: Timeout in seconds
        """
        print(f"DEBUG: Running event loop for {timeout}s")
        try:
            AppHelper.runConsoleEventLoop(timeout)
            print("DEBUG: Event loop cycle completed")
        except KeyboardInterrupt:
            print("DEBUG: KeyboardInterrupt in event loop")
            self._should_stop = True
            AppHelper.stopEventLoop()
        except Exception as e:
            print(f"DEBUG: Exception in event loop: {e}")
    
    def initialize(self) -> bool:
        """Initialize CoreBluetooth
        
        Returns:
            bool: True if initialization is successful
        """
        print("DEBUG: Entering initialize()")
        self._delegate = MacOSBeaconDelegate.alloc().initWithTransmitter_(self)
        self._peripheral_manager = CBPeripheralManager.alloc().initWithDelegate_queue_options_(
            self._delegate, None, None
        )
        print("DEBUG: Created delegate and peripheral_manager")
        print("DEBUG: Waiting for Bluetooth state update... (Press Ctrl+C to exit)")
        try:
            AppHelper.runConsoleEventLoop()
        except KeyboardInterrupt:
            print("DEBUG: KeyboardInterrupt, exiting event loop")
            AppHelper.stopEventLoop()
        return self._is_initialized
    
    def start_advertising(self, hwid: str, device_message: str) -> bool:
        """
        Start advertising LINE Simple Beacon (macOS specific)
        Args:
            hwid: Hardware ID (10 hex)
            device_message: Device message (hex)
        Returns:
            bool: True if advertising is started successfully
        """
        print("==== DEBUG: start_advertising called ====")
        if not self._is_initialized:
            print("DEBUG: Not initialized!")
            raise Exception("Not initialized")

        print(f"DEBUG: Bluetooth state: {self._peripheral_manager.state()}")
        if self._peripheral_manager.state() != 5:
            raise Exception("Bluetooth not powered on")

        try:
            print("DEBUG: Creating LINE Simple Beacon Service Data")
            service_data_bytes = BeaconCore.build_line_simple_beacon_service_data(hwid, device_message)
            print(f"DEBUG: Service Data (hex): {binascii.hexlify(service_data_bytes).decode()}")

            # assemble CoreBluetooth broadcasting data
            line_service_uuid_str = "FE6F"
            line_service_cbuuid = CBUUID.UUIDWithString_(line_service_uuid_str)
            beacon_nsdata = NSData.dataWithBytes_length_(service_data_bytes, len(service_data_bytes))

            adv_data = NSMutableDictionary.dictionary()
            service_uuids_key = NSString.stringWithString_("CBAdvertisementDataServiceUUIDsKey")
            service_data_key = NSString.stringWithString_("CBAdvertisementDataServiceDataKey")

            adv_data.setObject_forKey_([line_service_cbuuid], service_uuids_key)
            service_data_dict = NSMutableDictionary.dictionary()
            service_data_dict.setObject_forKey_(beacon_nsdata, line_service_uuid_str)
            adv_data.setObject_forKey_(service_data_dict, service_data_key)

            print(f"DEBUG: Advertising data: {adv_data}")

            print("DEBUG: Calling startAdvertising_")
            self._peripheral_manager.startAdvertising_(adv_data)
            print("DEBUG: startAdvertising_ called, waiting for callback")

            # wait for broadcasting to start
            timeout = 10  # seconds
            start_time = time.time()
            while not self._is_advertising and not self._should_stop:
                elapsed = time.time() - start_time
                print(f"DEBUG: Waiting... {elapsed:.1f}s (advertising: {self._is_advertising})")
                if elapsed > timeout:
                    print("DEBUG: Timeout waiting for advertising callback")
                    self._peripheral_manager.stopAdvertising()
                    break
                self._run_event_loop(0.5)

            if self._is_advertising:
                print("DEBUG: Advertising successfully started!")
                return True
            else:
                raise Exception("Advertising failed to start")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"DEBUG ERROR: {e}\n{error_details}")
            raise Exception(f"Advertising failed: {e}")
    
    def stop_advertising(self) -> bool:
        """Stop advertising
        
        Returns:
            bool: True if stopping is successful

        """
        if not self._is_advertising:
            return True
        
        try:
            self._peripheral_manager.stopAdvertising()
            self._set_advertising_state(False)
            return True
            
        except Exception as e:
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
