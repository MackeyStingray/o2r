
#Info and Configuration Commands
CMD_INFO = 20 # 0x14 # 1, rx len = ~264, tx no data
CMD_PING = 21 # 0x15 # 0, rx len = 12, tx no data
CMD_CONFIG = 22 # 0x16 # 2, rx len = 12, tx JSON
CMD_FACTORY_DEFAULT = 24 # 0x18 # 0, rx len = 12, tx no data

#Sensor Read / Realtime Data
CMD_READ_SENSORS = 23 # 0x17 # 3, rx len = 21, tx no data
CMD_RT_DATA = 27  # 0x1B rx len = ~275, tx no data
# CMD_PPG_RT_DATA = 28  # 0x1C 

#File Operations
CMD_FILE_OPEN = 3 # rx len = 12, tx filename length and filename
CMD_FILE_READ = 4 # tx block number
CMD_FILE_CLOSE = 5 # tx no data

# Additional commands discoverable at 
# https://github.com/viatomEcho/LepuBle/blob/2db64621969b436fcef5da992bd8728d72513b10/blepro/src/main/java/com/lepu/blepro/ble/cmd/OxyBleCmd.java#L19

BLE_MATCH_UUID = '00001801-0000-1000-8000-00805f9b34fb'
BLE_SERVICE_UUID = '14839ac4-7d7e-415c-9a42-167340cf2339'
BLE_READ_UUID = '0734594a-a8e7-4b1a-a6b1-cd5243059a57'
BLE_WRITE_UUID = '8b00ace7-eb0b-49b0-bbe9-9aee0a26e1a3'

TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'

RECORD_SIZE_v3 = 5

CSV_FIELDS = ( 'time', 'spo2', 'heartrate', 'motion', 'vibration', 'trailer' )
CSV_TITLES = { 'time': 'Time', 'spo2': 'SpO2(%)', 'heartrate': 'Pulse Rate(bpm)', 'motion': 'Motion', 'vibration': 'Vibration' }
CSV_TIMEFMT = '%I:%M:%S%p %b %d, %Y'

