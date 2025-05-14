## alt-line-simple-beacon (detector)

### notice

- this script is macOS only.

## Requirements for macOS

- Python 3.7+
- macOS 10.13+ (with Bluetooth LE support)
- [PyObjC](https://pyobjc.readthedocs.io/en/latest/) (`pip install pyobjc`)

### installation

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### scan BT devices near by

```
python3 detector.py
```
