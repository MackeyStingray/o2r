import o2r
import threading, time, queue, traceback
import argparse

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1', 'on'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0', 'off'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def str2bright(v):
    if v.lower() in ('l', '0'):
        return 0
    elif v.lower() in ('m', '1'):
        return 1
    elif v.lower() in ('h', '2'):
        return 2
    else:
        raise argparse.ArgumentTypeError('L/M/H or l/m/h or 0-2 expected.')

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="O2Ring BLE Downloader", epilog='Setting either --hr-alert-high or --hr-alert-low to 0 and leaving the other unset disables Heart Rate vibration alerts.  If one is 0 and the other is >0 then the 0 is ignored.')
    #arg_parser.add_argument('mac_address', help="MAC address of device to connect")
    arg_parser.add_argument( '-s', '--scan', help='Scan Time (Seconds)', type=int, metavar='[scan time]' )
    arg_parser.add_argument( '-v', '--verbose', help='increase output verbosity (repeat to increase)', action="count", default=0 )
    arg_parser.add_argument( '-e', '--ext', help='file extension for downloaded files (default: o2r)', default='o2r', metavar='EXT' )
    #arg_parser.add_argument( '--o2-alert', help='Enable/Disable O2 vibration alerts', type=str2bool, metavar='[bool]' )
    arg_parser.add_argument( '--o2-alert', help='O2 vibration alert at this %% (0-100, 0 = disabled)', type=int, metavar='[0-100]', choices=range(0,101) )
    #arg_parser.add_argument( '--hr-alert', help='Enable/Disable Heart Rate vibration alerts', type=str2bool, metavar='[bool]' )
    arg_parser.add_argument( '--hr-alert-high', help='Heart Rate High vibration alert (0-200, 0 = disabled)', type=int, metavar='[0-200]', choices=range(0,201) )
    arg_parser.add_argument( '--hr-alert-low', help='Heart Rate Low vibration alert (0-200, 0 = disabled)', type=int, metavar='[0-200]', choices=range(0,201) )
    arg_parser.add_argument( '--vibrate', help='Vibration Strength (1-100)', type=int, metavar='[1-100]', choices=range(1,101) )
    #arg_parser.add_argument( '--pedtar', help='Pedtar Setting (0-99999)', type=int, metavar='[0-99999]', choices=range(0,100000) )
    arg_parser.add_argument( '--screen', help='Enable/Disable "Screen Always On"', type=str2bool, metavar='[bool]' )
    arg_parser.add_argument( '--brightness', help='Screen Brightness (Low/Med/High)', type=str2bright, metavar='[L/M/H or 0-2]', choices=range(0,3) )

    args = arg_parser.parse_args()

    print(args)

    if( args.scan and args.scan > 0 ):
        stop_scanning_at = time.time() + args.scan
    else:
        stop_scanning_at = 0

    #print(sdfsdf.sdfdsf)
    print("Connecting...")

    manager = o2r.O2DeviceManager(adapter_name='hci0')
    manager.verbose = args.verbose + 1
    manager.queue = queue.Queue()

    server4t = threading.Thread(target=manager.run)
    server4t.setDaemon(True)
    server4t.start()

    #manager.start_discovery( dbus.Array([dbus.String('00001801-0000-1000-8000-00805f9b34fb')]) )
    manager.start_discovery()

    rings = {}
    want_exit = False
    run = True

    try:
        while run:
            try:
                d = manager.queue.get(True, 1)
            except queue.Empty:
                d = None
            except KeyboardInterrupt:
                if( want_exit ):
                    traceback.print_exc()
                    run = False
                    break
                print('Shutting Down')
                want_exit = True
                manager.stop_discovery()
                for r in rings:
                    rings[r].close()
            except:
                traceback.print_exc()
                run = False
                manager.stop_discovery()
                break

            if( d is None ):
                pass
            elif( d[1] is 'READY' ):
                if( d[0] in rings ):
                    rings[d[0]].close()
                rings[d[0]] = o2r.o2state( d[0], d[2], args )
            elif( d[1] is 'DISCONNECT' ):
                del rings[d[0]]
            elif( d[1] is 'BTDATA' ):
                rings[d[0]].recv( d[2] )
            else:
                print('unhandled:', d)

            for r in rings:
                if( rings[r].dev.pkt is None ):
                    rings[r].check()

            if( want_exit and len(rings) == 0 ):
                run = False
                #break

            if( (stop_scanning_at > 0) and (stop_scanning_at <= time.time()) ):
                stop_scanning_at = 0
                manager.stop_discovery()
                if( len(rings) < 1 ):
                    print('No devices found!')
                    want_exit = True
                    run = False
    except:
        traceback.print_exc()

    #print(manager.devices())
    print('disconnecting')
    #device.disconnect()
    for dev in manager.devices():
        print('disconnecting', dev.mac_address)
        dev.disconnect()

    time.sleep(1)

    print('stopping')
    manager.stop()

    print('joining')
    print(server4t.join(5))
