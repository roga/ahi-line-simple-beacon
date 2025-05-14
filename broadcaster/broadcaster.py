import sys
import argparse
from core.beacon_core import BeaconCore
import platform
import time

def get_platform_transmitter():
    """Return the corresponding broadcasting device implementation based on the operating system"""
    system = platform.system().lower()
    
    if system == 'darwin':  # macOS
        from platforms.macos import MacOSTransmitter
        return MacOSTransmitter()
    elif system == 'linux':
        from platforms.linux import LinuxTransmitter
        return LinuxTransmitter()
    else:
        raise Exception(f"Unsupported operating system: {system}")

def main():
    parser = argparse.ArgumentParser(
        description='LINE Simple Beacon broadcasting data generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create broadcasting data with default value
  python broadcaster.py --hwid 0123456789

  # Create broadcasting data with device message
  python broadcaster.py --hwid 0123456789 --message 0123456789ABCDEF
        """
    )
    
    parser.add_argument(
        '--hwid',
        required=True,
        help='Hardware ID (10 hexadecimal characters)'
    )
    
    parser.add_argument(
        '--message',
        default='',
        help='Device message (hexadecimal string, up to 13 bytes)'
    )
    
    args = parser.parse_args()
    
    try:
        # check hwid length
        if len(args.hwid) != 10 or not all(c in '0123456789abcdefABCDEF' for c in args.hwid):
            raise Exception("HWID must be 10 hexadecimal characters")

        # check device_message length
        if len(args.message) % 2 != 0:
            raise Exception("Device message must be an even length hexadecimal string (each two characters represent 1 byte)")

        # get the corresponding platform transmitter
        transmitter = get_platform_transmitter()

        # initialize and start broadcasting
        if not transmitter.initialize():
            raise Exception("Failed to initialize transmitter")

        if not transmitter.start_advertising(args.hwid, args.message):
            raise Exception("Failed to start advertising")
        
        try:
            print("Running, press CTRL+C to stop...")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            transmitter.stop_advertising()
            print("broadcaster stopped")

        # output result
        print(f"HWID: {args.hwid}")
        print(f"Device message: {args.message}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
