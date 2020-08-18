# Python BLE client for Wellue / Viatom pulse oximeters
This Python app downloads files from and reconfigures settings on Wellue O2Ring / Viatom Health Ring pulse oximeters.  It requires the [Bluetooth GATT SDK for Python](https://github.com/getsenic/gatt-python) which in turn requires D-Bus and Bluez and thus currently only supports Linux.

### Prerequisites
[Python 3.4+](https://www.python.org) and [Bluetooth GATT SDK for Python](https://github.com/getsenic/gatt-python)

### Installing
On Debian Buster all I had to do to install the GATT SDK was 
```
sudo apt-get install python3-dbus
sudo pip3 install gatt
```
To run this app just download it and run `python3 o2ring.py`.  Currently the settings need to be passed on the command line
```
$ python3 o2ring.py -h
usage: o2ring.py [-h] [-v] [-s [scan time]] [-m] [-p PREFIX] [-e EXT]
                 [--o2-alert [0-100]] [--hr-alert-high [0-200]]
                 [--hr-alert-low [0-200]] [--vibrate [1-100]]
                 [--screen [bool]] [--brightness [L/M/H or 0-2]]

O2Ring BLE Downloader

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity (repeat to increase)
  -s [scan time], --scan [scan time]
                        Scan Time (Seconds, 0 = forever, default = 15)
  -m, --multi           Keep scanning for multiple devices
  -p PREFIX, --prefix PREFIX
                        Downloaded file prefix (default: "[BT Name] - ")
  -e EXT, --ext EXT     Downloaded file extension (default: o2r)
  --o2-alert [0-100]    O2 vibration alert at this % (0-100, 0 = disabled)
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
$ python3 o2ring.py
Connecting...
Adding device c8:07:5f:xx:xx:xx
[c8:07:5f:xx:xx:xx] Discovered: O2Ring 45xx
[O2Ring 45xx] New RSSI: -54
[O2Ring 45xx] New RSSI: -63
[O2Ring 45xx] Connected
Starting up for c8:07:5f:xx:xx:xx
[O2Ring 45xx] Config:
{     'Application': '',
      'BootloaderVer': '1.0.0.0',
      'BranchCode': '24010000',
      'CurBAT': '97%',
      'CurBatState': '0',
      'CurMode': '0',
      'CurMotor': '40',
      'CurOxiThr': '85',
      'CurPedtar': '99999',
      'CurState': '1',
      'CurTIME': '2020-08-17,23:29:30',
      'FileList': '20200817095111,20200817225251,',
      'FileVer': '3',
      'HRHighThr': '125',
      'HRLowThr': '55',
      'HRSwitch': '0',
      'HardwareVer': 'AA',
      'LightStr': '0',
      'LightingMode': '0',
      'Model': '1652',
      'OxiSwitch': '1',
      'Region': 'CE',
      'SN': '20xxxx45xx',
      'SPCPVer': '1.3',
      'SoftwareVer': '1.4.0'}
[O2Ring 45xx] Time off by 11 seconds, updating
[O2Ring 45xx] File List is now ['20200817095111', '20200817225251']
[O2Ring 45xx] Already Have File "O2Ring 45xx - 20200817095111.o2r"
[O2Ring 45xx] Requesting File 20200817225251, saving to "O2Ring 45xx - 20200817225251.o2r"
[O2Ring 45xx] File 20200817225251 Opened, Size 1750 -----------------------------------------------|
|==================================================================================================|
[O2Ring 45xx] O2  98%, HR  81, Perfusion Idx   0, motion   0, batt  97%
[O2Ring 45xx] O2  98%, HR  81, Perfusion Idx   0, motion   0, batt  97%
[O2Ring 45xx] O2  98%, HR  81, Perfusion Idx   0, motion   0, batt  97%
[O2Ring 45xx] O2  98%, HR  81, Perfusion Idx   0, motion   0, batt  97%
[O2Ring 45xx] O2  98%, HR  81, Perfusion Idx   0, motion   0, batt  97%
[O2Ring 45xx] O2  98%, HR  81, Perfusion Idx   0, motion   0, batt  97%
[O2Ring 45xx] O2  98%, HR  81, Perfusion Idx  11, motion   0, batt  97%
[O2Ring 45xx] O2  98%, HR  80, Perfusion Idx   9, motion   0, batt  97%
```
### Known issues
Logging of realtime data is not implemented yet, and neither is converting the downloaded files to a readable format such as CSV; [OSCAR](https://www.sleepfiles.com/OSCAR) should be able to import the binary files though.
