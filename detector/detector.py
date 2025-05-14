import platform
import sys

if platform.system().lower() != 'darwin':
    print("Error: This program is only available on macOS")
    sys.exit(1)

import objc;
from Foundation import NSObject, NSRunLoop, NSDate
import CoreBluetooth
import curses
import time
import os
import csv

objc.loadBundle("CoreBluetooth", globals(), bundle_path="/System/Library/Frameworks/CoreBluetooth.framework")
CBCentralManager = objc.lookUpClass("CBCentralManager")
CBPeripheral = objc.lookUpClass("CBPeripheral")

devices = {}

class MyDelegate(NSObject):
    def init(self):
        self = objc.super(MyDelegate, self).init()
        if self is None:
            return None
        self.centralManager = CBCentralManager.alloc().initWithDelegate_queue_options_(self, None, None)
        return self

    def centralManagerDidUpdateState_(self, central):
        if central.state() == 5:
            self.centralManager.scanForPeripheralsWithServices_options_(None, None)
	
    def centralManager_didDiscoverPeripheral_advertisementData_RSSI_(self, central, peripheral, advData, RSSI):
        name = peripheral.name() or "Unknown"
        uuid = peripheral.identifier().UUIDString()
        manufacturer_data = advData.get("kCBAdvDataManufacturerData")

        if manufacturer_data:
            raw_bytes = manufacturer_data.bytes().tobytes()
            hex_str = raw_bytes.hex().upper()
            if len(raw_bytes) >= 2:
                cid_le = raw_bytes[0] + (raw_bytes[1] << 8)  # Little-endian
                cid_str = f"{cid_le:04X}"
            else:
                cid_str = "N/A"
        else:
            hex_str = "N/A"
            cid_str = "N/A"

        company_name = cid_map.get(cid_str, "Unknown")
        devices[uuid] = {
            'name': name,
            'uuid': uuid,
            'rssi': RSSI,
            'manufacturer': hex_str,
            'company_id': cid_str,
            'company_name': company_name
        }

def load_cid_map(filename='cid.csv'):
    cid_map = {}
    if not os.path.exists(filename):
        return cid_map

    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                cid_hex = row[0].strip().lower().replace('0x', '')
                cid_hex = cid_hex.zfill(4).upper()
                company = row[1].strip().strip('"')
                cid_map[cid_hex] = company
    return cid_map

def curses_main(stdscr):
    delegate = MyDelegate.alloc().init()
    curses.curs_set(0)
    stdscr.nodelay(True)

    sort_modes = [
        ('RSSI high → low', lambda d: sorted(d.values(), key=lambda x: x['rssi'], reverse=True)),
        ('RSSI low → high', lambda d: sorted(d.values(), key=lambda x: x['rssi'])),
        ('CID z → a', lambda d: sorted(d.values(), key=lambda x: x['company_id'], reverse=True)),
        ('CID a → z', lambda d: sorted(d.values(), key=lambda x: x['company_id'])),
    ]
    sort_idx = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        sort_title, sort_func = sort_modes[sort_idx]
        stdscr.addstr(0, 0, f"LITE-SIMPLE-BEACON Detector ({sort_title}) | o: Sort Order | Ctrl+C to exit")
        stdscr.addstr(1, 0, "-" * (width - 1))

        # Sort devices by current sort mode
        sorted_devices = sort_func(devices)

        for i, device in enumerate(sorted_devices, start=2):
            if i >= height - 1:
                break
            name = device['name'][:20]
            rssi = device['rssi']
            uuid = device['uuid'][:8]
            manuf = device['manufacturer'][:32]
            line = (
                f"{name:<20} RSSI: {rssi:<4} UUID: {uuid} "
                f"CID: {device['company_id']} ({device['company_name']}) MANUF: {manuf}"
            )
            stdscr.addstr(i, 0, line[:width - 1])

        stdscr.refresh()
        NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))
        time.sleep(0.9)

        # Process key
        try:
            key = stdscr.getch()
            if key == ord('o') or key == ord('O'):
                sort_idx = (sort_idx + 1) % len(sort_modes)
        except Exception:
            pass

cid_map = load_cid_map() 

if __name__ == "__main__":
    try:
        curses.wrapper(curses_main)
    except KeyboardInterrupt:
        curses.endwin() 
        print("\nStop Scanning.\n")
    except Exception as e:
        curses.endwin()
        print("\nStop Scanning.\n")
        raise
