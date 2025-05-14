## alt-line-simple-beacon (broadcaster)

A cross-platform command-line tool for broadcasting [LINE Simple Beacon](https://github.com/line/line-simple-beacon) signals using Bluetooth Low Energy (BLE).

## Requirements for macOS

- Python 3.7+
- macOS 10.13+ (with Bluetooth LE support)
- [PyObjC](https://pyobjc.readthedocs.io/en/latest/) (`pip install pyobjc`)

## Requirements for Linux

- Python 3.7+

## Installation

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```
python simplebeacon.py --hwid <HWID> [--message <DEVICE_MESSAGE>]
```

- `--hwid`: **Required**, 10 hexadecimal characters (5 bytes), obtain from LINE Official Account Manager.
- `--message`: **Optional**, hexadecimal string of 1~13 bytes, used as custom device message.

### Example

```bash
python broadcaster.py --hwid 018741a0bd --message 012345
```

After starting, the program will continue broadcasting until you press `Ctrl+C` to stop.

## References

- [LINE Simple Beacon Spec](https://github.com/line/line-simple-beacon/blob/master/README.en.md)

