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
    arg_parser.add_argument( '-v', '--verbose', help='increase output verbosity (repeat to increase)', action="count", default=0 )
    arg_parser.add_argument( '-s', '--scan', help='Scan Time (Seconds, 0 = forever, default = 15)', type=int, metavar='[scan time]', default=15 )
    arg_parser.add_argument( '--keep-going', help='Do not disconnect when finger is not present', action="store_true" )
    arg_parser.add_argument( '-m', '--multi', help='Keep scanning for multiple devices', action="store_true" )
    arg_parser.add_argument( '-p', '--prefix', help='Downloaded file prefix (default: "[BT Name] - ")', metavar='PREFIX' )
    arg_parser.add_argument( '-e', '--ext', help='Downloaded file extension (default: vld)', default='vld', metavar='EXT' )
    arg_parser.add_argument( '--csv', help='Convert downloaded file to CSV', action="store_true" )

    # the O2Ring changes the o2 alert value to 90 if >95 is provided
    #arg_parser.add_argument( '--o2-alert', help='Enable/Disable O2 vibration alerts', type=str2bool, metavar='[bool]' )
    arg_parser.add_argument( '--o2-alert', help='O2 vibration alert at this %% (0-95, 0 = disabled)', type=int, metavar='[0-95]', choices=range(0,101) )

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

    print("Connecting...")

    manager = o2r.O2DeviceManager(adapter_name='hci0')
    manager.verbose = args.verbose + 1
    manager.queue = queue.Queue()

    manager_thread = threading.Thread(target=manager.run)
    manager_thread.setDaemon(True)
    manager_thread.start()

    #manager.start_discovery( ['00001801-0000-1000-8000-00805f9b34fb'] )
    manager.start_discovery()
    scanning = True
    multi = args.multi
    rings = {}
    want_exit = False
    run = True

    try:
        while run:
            try:
                cmd = manager.queue.get(True, 1)
            except queue.Empty:
                cmd = None
            except KeyboardInterrupt:
                if( want_exit ):
                    traceback.print_exc()
                    run = False
                    break
                print('Shutting Down')
                want_exit = True
                manager.stop_discovery()
                scanning = False
                for r in rings:
                    rings[r].close()

                del rings
                rings = {}
            except:
                traceback.print_exc()
                run = False
                if( scanning ):
                    manager.stop_discovery()
                    scanning = False
                break

            if( cmd is None ):
                pass
            else:
                (ident, command, data) = cmd

                if( command is 'READY' ):
                    if( 'verbose' not in data ):
                        data['verbose'] = args.verbose + 1
                    if( ident in rings ):
                        rings[ident].close()
                    rings[ident] = o2r.o2state( data['name'], data, args )
                    if( not multi ):
                        manager.stop_discovery()
                        scanning = False
                elif( command is 'DISCONNECT' ):
                    rings[ident].close()
                    del rings[ident]
                    if( (not scanning) and len(rings) < 1 ):
                        want_exit = True
                elif( command is 'BTDATA' ):
                    rings[ident].recv( data )
                else:
                    print('unhandled command:', cmd)

            for r in rings:
                #if( rings[r].dev.pkt is None ):
                rings[r].check()

            if( want_exit and len(rings) == 0 ):
                run = False
                #break

            if( (stop_scanning_at > 0) and (stop_scanning_at <= time.time()) ):
                stop_scanning_at = 0
                scanning = False
                manager.stop_discovery()
                if( len(rings) < 1 ):
                    print('No devices found!')
                    want_exit = True
                    run = False
    except:
        traceback.print_exc()

    if( scanning ):
        manager.stop_discovery()

    #print(manager.devices())
    print('disconnecting all')
    for dev in manager.devices():
        if( dev.is_connected() ):
            print('disconnecting:', dev.mac_address)
            dev.disconnect()

    time.sleep(0.5)

    print('stopping')
    manager.stop()

    print('joining')
    print(manager_thread.join(5))
