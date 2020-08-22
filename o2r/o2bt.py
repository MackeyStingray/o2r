import gatt
from gatt import errors
import dbus
import struct
import queue

from .defines import *

class O2BTDevice(gatt.Device):
    def busy( self ):
        return self.pkt is not None

    def send_packet( self, pkt ):
        self.pkt_queue.put( pkt )
        self._start_packet()

    def _start_packet( self ):
        if self.pkt is None:
            try:
                self.pkt = self.pkt_queue.get(False)
            except:
                pass

            if self.pkt is not None:
                pstr = self.pkt.packetify()
                self._send_buf = pstr

                if( (self.verbose or self.manager.verbose) > 3 ):
                    print('[%s] Sending' % self.name, pstr.hex())

                if( len( pstr ) > 20 ):
                    self.write.write_value( pstr[:20] )
                    self._send_buf = pstr[20:]
                else:
                    self.write.write_value( pstr )
                    self._send_buf = ""

    def advertised(self):
        if self.notified:
            return

        self.notified = True
        super().advertised()

        self.name = self.alias()
        print("[%s] Discovered: %s" % (self.mac_address, self.name) )

        if( len(self.name) < 4 ):
            self.name = self.mac_address

        if( (self.verbose or self.manager.verbose) > 1 ):
            #for i in ('Name','Icon','Class','RSSI', 'UUIDs'):
            for i in ('UUIDs',):
                if i is not None:
                    if i is 'UUIDs':
                        print("%s:" % (i), ' '.join(self.get_prop(i)) )
                    else:
                        print("%s:" % (i), self.get_prop(i) )

            #print('')

        self.connect()

    def properties_changed(self, sender, changed_properties, invalidated_properties):
        super().properties_changed( sender, changed_properties, invalidated_properties )

        #print("[%s] Property Changed" % (self.mac_address))
        #print( sender )
        #print( changed_properties )
        #print( invalidated_properties )

        if( (self.verbose or self.manager.verbose) < 1 ):
            return

        for i in changed_properties:
            if( i == "RSSI" ):
                print( "[%s] New RSSI: %s" % (self.name, changed_properties[i]) )
                self.rssi = changed_properties[i]
            elif( i in ("Connected","ServicesResolved") ):
                pass
            else:
                print( "[%s] Property %s Changed: %s" % (self.name, i, changed_properties[i]) )

    def connect_succeeded(self):
        super().connect_succeeded()
        print("[%s] Connected" % (self.name))

    def connect_failed(self, error):
        super().connect_failed(error)
        print("[%s] Connection failed: %s" % (self.name, str(error)))

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        print("[%s] Disconnected" % (self.name))

    def services_resolved(self):
        super().services_resolved()

        if( (self.verbose or self.manager.verbose) > 1 ):
            print("[%s] Resolved services" % (self.name))
            for service in self.services:
                print("[%s]\tService [%s]" % (self.name, service.uuid))
                for characteristic in service.characteristics:
                    print("[%s]\t\tCharacteristic [%s]" % (self.name, characteristic.uuid))
                    if hasattr( characteristic, 'descriptors'):
                        for descriptor in characteristic.descriptors:
                            print("[%s]\t\t\tDescriptor [%s] (%s)" % (self.name, descriptor.uuid, descriptor.read_value()))

        for s in self.services:
            if s.uuid == BLE_SERVICE_UUID:
                for c in s.characteristics:
                    if c.uuid == BLE_READ_UUID:
                        c.enable_notifications()
                        #(self.queue or self.manager.queue).put((self.mac_address, 'READY', self))
                    elif c.uuid == BLE_WRITE_UUID:
                        self.write = c


    def descriptor_read_value_failed(self, descriptor, error):
        print( '[%s]' % self.name, 'descriptor_value_failed:', descriptor, error)

    def characteristic_value_updated(self, characteristic, value):
        if( (self.verbose or self.manager.verbose) > 2 ):
            if( (characteristic.uuid != BLE_READ_UUID) or ((self.verbose or self.manager.verbose) > 4) ):
                print( '[%s]' % self.name, 'Characteristic', characteristic.uuid, 'updated:', value)

        if( not self.pkt ):
            print('[%s]' % self.name, "Received unexpected data!", value, characteristic)
            return

        res = self.pkt.recv( value )
        if res is False: # waiting for more data
            if( (self.verbose or self.manager.verbose) > 4 ):
                print( '[%s] Need more data' % self.name )
            return

        if( (self.verbose or self.manager.verbose) > 3 ):
            print('[%s] Final recv:' % self.name, self.pkt.recv_buf.hex())

        (self.queue or self.manager.queue).put((self.mac_address, 'BTDATA', self.pkt))
        self.pkt = None
        self._start_packet()


    def characteristic_write_value_failed(self, characteristic, error):
        print('[%s] Characteristic' % self.name, characteristic.uuid, 'write value failed:', error)

    def	characteristic_write_value_succeeded(self, characteristic):
        if( (self.verbose or self.manager.verbose) > 4 ):
            print('[%s] Characteristic' % self.name, characteristic.uuid, 'write value ok')

        if( len( self._send_buf ) > 0 ):
            self.write.write_value( self._send_buf[:20] )
            if( len( self._send_buf ) > 20 ):
                self._send_buf = self._send_buf[20:]
            else:
                self._send_buf = ""


    def characteristic_enable_notifications_failed(self, characteristic, error):
        print('[%s] Characteristic' % self.name, characteristic.uuid, 'enable notifications failed:', error)

    def characteristic_enable_notifications_succeeded(self, characteristic):
        if( (self.verbose or self.manager.verbose) > 3 ):
            print('[%s] Characteristic' % self.name, characteristic.uuid, 'enable notifications ok')

        self.name = self.alias() or self.mac_address
        if( len(self.name) < 4 ):
            self.name = self.mac_address

        (self.queue or self.manager.queue).put((self.mac_address, 'READY', {'name':self.name, 'mac':self.mac_address, 'self':self, 'verbose':(self.verbose or self.manager.verbose), 'send':self.send_packet, 'busy':self.busy}))


    def disconnect_succeeded( self ):
        super().disconnect_succeeded()
        (self.queue or self.manager.queue).put((self.mac_address, 'DISCONNECT', self))

    def get_prop(self, prop):
        """
        Returns the device's name.
        """
        try:
            return self._properties.Get('org.bluez.Device1', prop)
        except dbus.exceptions.DBusException as e:
            if e.get_dbus_name() == 'org.freedesktop.DBus.Error.UnknownObject' or e.get_dbus_name() == 'org.freedesktop.DBus.Error.InvalidArgs':
                # BlueZ sometimes doesn't provide an alias, we then simply return `None`.
                # Might occur when device was deleted as the following issue points out:
                # https://github.com/blueman-project/blueman/issues/460
                return None
            else:
                raise _error_from_dbus_error(e)

class O2DeviceManager(gatt.DeviceManager):
    def update_devices(self):
        pass

#    def device_discovered(self, device):
#        print("Adding device (Stage 2)") #, device.mac_address)
#        device.notified = False
#
#
#        super().device_discovered(device)

    def make_device(self, mac_address):
        dev = O2BTDevice(mac_address=mac_address, manager=self, managed=False)
        valid = False
        dev.name = dev.alias() or mac_address
        dev.notified = False
        dev.rssi = -999
        dev.verbose = None
        dev.queue = None
        dev.write = None
        dev.pkt = None

        uuids = dev.get_prop('UUIDs')

        if( self.verbose > 4 ):
            print('Considering', mac_address, dev.name, uuids, valid)

        if uuids is not None and BLE_MATCH_UUID in uuids and BLE_SERVICE_UUID in uuids:
            valid = True
        else:
            # We might not have the list of UUIDs yet, so also check by name
            names = ( 'Checkme_O2', 'CheckO2', 'SleepU', 'SleepO2', 'O2Ring', 'WearO2', 'KidsO2', 'BabyO2', 'Oxylink' )
            for n in names:
                if( n in dev.name ):
                    if( self.verbose > 1 ):
                        print( 'Found device by name:', n )

                    valid = True
                    break

        if valid:
            print("Adding device", mac_address)
            #dev.connect()
            dev.pkt_queue = queue.Queue()
            self._manage_device( dev )
            return dev

        del dev
        return None

def _error_from_dbus_error(e):
    return {
        'org.bluez.Error.Failed': errors.Failed(e.get_dbus_message()),
        'org.bluez.Error.InProgress': errors.InProgress(e.get_dbus_message()),
        'org.bluez.Error.InvalidValueLength': errors.InvalidValueLength(e.get_dbus_message()),
        'org.bluez.Error.NotAuthorized': errors.NotAuthorized(e.get_dbus_message()),
        'org.bluez.Error.NotPermitted': errors.NotPermitted(e.get_dbus_message()),
        'org.bluez.Error.NotSupported': errors.NotSupported(e.get_dbus_message()),
        'org.freedesktop.DBus.Error.AccessDenied': errors.AccessDenied("Root permissions required"),
        'org.freedesktop.DBus.Error.InvalidArgs': errors.Failed(e.get_dbus_message())
    }.get(e.get_dbus_name(), errors.Failed(e.get_dbus_message()))

