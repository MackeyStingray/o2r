# Python BLE client for Wellue / Viatom pulse oximeters (FORK, uses bleak)

It is a fork of [project of same name](https://github.com/MackeyStingray/o2r) to support bleak for use on Windows and maybe Mac in addition to Linux.
Kudos to the original author for figuring out all the BLE stuff and writing an awesome program.

The thread (and post) on apneaboard that discusses some stuff relating to o2ring and o2r: [http://www.apneaboard.com/forums/Thread-Added-a-new-pulse-oximeter-importer?pid=388834#pid388834](http://www.apneaboard.com/forums/Thread-Added-a-new-pulse-oximeter-importer?pid=388834#pid388834).

The license is unchanged (GPLv3 License).

This Python app downloads files from and reconfigures settings on Wellue O2Ring / Viatom Health Ring pulse oximeters. It requires the [Bluetooth Low Energy platform Agnostic Klient (bleak)](https://github.com/hbldh/bleak).

### Prerequisites

 - Windows: [Python 3.6-3.8](https://www.python.org) and [Bluetooth Low Energy platform Agnostic Klient (bleak)](https://github.com/hbldh/bleak). It did not work on Python 3.9 on Windows for me.
 - macOS: Working on Python 3.9.14 on macOS

### Installing

Install prerequisite `bleak`

```
pip install -r requirements.txt
#sudo pip3 install bleak #Alternative, to get latest Bleak
```

To run this app download it and run `python3 o2ring.py`. Settings get passed as command line switches:

```
$python o2ring.py -h
usage: o2ring.py [-h] [-v] [-s [scan time]] [--keep-going] [-m] [-p PREFIX]
                 [-e EXT] [--csv] [--realtime] [--o2-alert [0-95]]
                 [--hr-alert-high [0-200]] [--hr-alert-low [0-200]]
                 [--vibrate [1-100]] [--screen [bool]]
                 [--brightness [L/M/H or 0-2]]

O2Ring BLE Downloader

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity (repeat to increase)
  -s [scan time], --scan [scan time]
                        Scan Time (Seconds, 0 = forever, default = 30)
  --keep-going          Do not disconnect when finger is not present
  -m, --multi           Keep scanning for multiple devices
  -p PREFIX, --prefix PREFIX
                        Downloaded file prefix (default: "[BT Name] - ")
  -e EXT, --ext EXT     Downloaded file extension (default: vld)
  --csv                 Convert downloaded file to CSV
  --realtime            Enable Realtime PPG data capture
  --o2-alert [0-95]     O2 vibration alert at this % (0-95, 0 = disabled)
  --hr-alert-high [0-200]
                        Heart Rate High vibration alert (0-200, 0 = disabled)
  --hr-alert-low [0-200]
                        Heart Rate Low vibration alert (0-200, 0 = disabled)
  --vibrate [1-100]     Vibration Strength (1-100)
  --screen [bool]       Enable/Disable "Screen Always On"
  --brightness [L/M/H or 0-2]
                        Screen Brightness (Low/Med/High)

Setting either --hr-alert-high or --hr-alert-low to 0 and leaving the other
unset disables Heart Rate vibration alerts. If one is 0 and the other is >0
then the 0 is ignored.
```

```
$ python3 o2ring.py --csv --keep-going
```


### Realtime Collection
Since the ring only stores data at the 4-second resolution in files, if you want access to the raw PPG/pleth 125Hz waveform you need to keep a BLE connection active with the ring.  Pass the `--realtime` switch to record realtime data.

```
$ python3 o2ring.py --realtime
```

This will output data to timestamped `.rt` files in the current directory.

#### .rt file format 
The .rt file is structured as a 27-char timestamp, a `|` and then a 274-char hex string.
First get the hex string and convert from 274 hex to 137 `bytes`.
The bytes are a `struct` of the form `<2BxBx2B5x125s` which is interpreted as:
 - 1 byte SpO2
 - 1 byte Heart Rate
 - null byte
 - 1 byte Battery
 - null byte
 - 1 byte Activity/Motion
 - 6 bytes ignore/null
 - 125 bytes of PPG/pleth samples @ 125Hz, so 1 second of samples
 

One way you could parse a `.rt` file is e.g.: 
```
filename = "<name_timestamp>.rt"
with open(filename, "r") as f:
    text = f.read().splitlines()
for line in text:
    line = line.zfill(301)[27:] #Ensure the correct # of bytes for the struct
    spo2, hr, battery, activity, _, ppg_bytes = struct.unpack("<2BxBx2B5x125s", bytes.fromhex(line))
    ppg = [x for x in ppg_bytes]
```

### Known issues

- N/A
