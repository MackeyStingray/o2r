import time, json, pprint, struct, os.path, datetime

from .defines import *
from .o2pkt import o2pkt
from .o2cmd import o2cmd

class o2state:
    def __init__( self, mac, device, args ):
        self.name = mac
        self.dev = device
        self.args = args
        self.next_read = 0
        self.need_cfg = False
        self.quiet_cfg = False
        self.want_files = []
        self.read_file = None
        self.read_block = None
        self.read_fp = None
        self.read_size = 0
        self.read_want = 0
        print('Starting up for', mac)

        self.dev.send_packet( o2pkt(CMD_INFO) )
        self.req_time_str = time.strftime( TIME_FORMAT )
        #self.dev.send_packet( o2pkt(CMD_PING) )
        #self.dev.send_packet( o2pkt(CMD_READ_SENSORS) )

    def recv( self, pkt ):
        if( (self.dev.verbose or self.dev.manager.verbose) > 2 ):
            print( '[%s]' % self.dev.name, pkt.recv_data.hex() )

        if( pkt.recv_cmd != 0 ):
            print( '[%s] Command %d Failed!' % (self.dev.name, pkt.cmd), pkt.recv_buf.hex() )

        if( pkt.cmd == CMD_READ_SENSORS ):
            self.next_read = time.time() + 2.0

            # ffffff00000000600005000000
            # ffffff00000000620100000000
            # 624200000000006100920a0100
            # oohh..........bbccmmaaff..

            #(o2, hr, u1, u2) = struct.unpack( '<BBBB', pkt.recv_data )

            o2 = int(pkt.recv_data[0])
            hr = int(pkt.recv_data[1])
            # [2]
            # [3]
            # [4]
            # [5]
            # [6]
            batt = int(pkt.recv_data[7])
            charging = int( pkt.recv_data[8] )
            motion = int(pkt.recv_data[9])
            hr_strength = int(pkt.recv_data[10]) # heart rate signal strength
            finger_present = bool( pkt.recv_data[11] )
            # [12]

            #batts = str(batt) + '%' + ('++' if charging else '')

            if( charging > 0 ):
                if( charging == 1 ):
                    batts = str(batt) + '%++'
                elif( charging == 2 ):
                    batts = 'CHGD'
                else:
                    batts = ('% 3d' % batt) + '%-' + str(charging)

            else:
                batts = ('% 3d' % batt) + '%'

            print( '[%s] SpO2 %3d%%, HR %3d bpm, Perfusion Idx %3d, motion %3d, batt %s' % (self.dev.name, o2, hr, hr_strength, motion, batts) )

            if( (o2 > 100) or (o2 < 10) or (not finger_present) ):
                self.quiet_cfg = True
                self.dev.send_packet( o2pkt(CMD_INFO) )
                self.req_time_str = time.strftime( TIME_FORMAT )
                
        elif( pkt.cmd == CMD_INFO ):
            self.current_cfg = json.loads( pkt.recv_data.decode('ascii').rstrip( ' \t\r\n\0' ) )

            if( not self.quiet_cfg ):
                pp = pprint.PrettyPrinter(indent=6)
                print( '[%s] Config:' % self.dev.name )
                pp.pprint( self.current_cfg )

            o2_time = datetime.datetime(*time.strptime( self.current_cfg['CurTIME'], TIME_FORMAT )[:6])
            sent_time = datetime.datetime(*time.strptime( self.req_time_str, TIME_FORMAT )[:6])
            tdelta = (o2_time - sent_time).total_seconds()

            if( abs(tdelta) > 10 ):
                print( '[%s] Time off by %d seconds, updating' % (self.dev.name, tdelta) )
                self.dev.send_packet( o2cmd.SetTime() )

            if( not self.need_cfg ):
                self.check_settings( )
            else:
                self.need_cfg = False

            self.add_files( self.current_cfg['FileList'] )
            self.get_file()

            if( (self.next_read < 1) and (self.read_file is None) ):
                self.next_read = time.time() + 1.0

        elif( pkt.cmd == CMD_FILE_OPEN ):
            if( pkt.recv_cmd != 0 ):
                print( '[%s] File Open Failed!' % self.dev.name, self.read_file )
                self.dev.send_packet( o2pkt(CMD_FILE_CLOSE) )
                self.next_read = time.time() + 2.0
                return

            self.read_block = 0
            self.next_read = 0
            self.read_want = self.read_size = struct.unpack( '<I', pkt.recv_data )[0]
            if( (self.dev.verbose or self.dev.manager.verbose) > 0 ):
                ostr = '[%s] File %s Opened, Size %d ' % (self.dev.name, self.read_file, self.read_size)
                pad = 99 - len(ostr)
                if( pad > 0 ):
                    ostr += ('-' * pad) + '|'
                print( ostr )
                print( '|', end='')
                self.read_percent = 1
            self.dev.send_packet( o2pkt(CMD_FILE_READ, block=self.read_block) )
            self.read_fp = open( self.read_file, 'wb' )
        elif( pkt.cmd == CMD_FILE_READ ):
            self.read_want -= len( pkt.recv_data )
            self.read_block += 1
            cur_percent = round(((self.read_size - self.read_want) / self.read_size) * 100)
            if( ((self.dev.verbose or self.dev.manager.verbose) > 0) and (cur_percent != self.read_percent) ):
                padc = ''
                if( cur_percent == 100 ):
                    pad = 99 - self.read_percent
                    if( pad > 0 ):
                        padc = '=' * pad
                    padc += '|'
                    print( padc, flush=True )
                else:
                    pad = cur_percent - self.read_percent
                    padc = '=' * pad
                    print( padc, end='', flush=True)

            self.read_percent = cur_percent

            if( self.read_want > 0 ):
                self.next_read = 0
                self.dev.send_packet( o2pkt(CMD_FILE_READ, block=self.read_block) )
                if( (self.dev.verbose or self.dev.manager.verbose) > 2 ):
                    print( '[%s] %d remaining' % (self.dev.name, self.read_want) )
                if( self.read_fp ):
                    self.read_fp.write(pkt.recv_data)
            else:
                self.dev.send_packet( o2pkt(CMD_FILE_CLOSE) )
                if( self.read_fp ):
                    self.read_fp.write(pkt.recv_data)
                    self.read_fp.close()
                self.read_fp = None
                self.read_file = None
                self.get_file()

            if( (self.dev.verbose or self.dev.manager.verbose) > 3 ):
                # here self.read_block is +1 which displays nicer
                print( '[%s] Block %d File Data:' % (self.dev.name, self.read_block), pkt.recv_data.hex() )
        elif( pkt.cmd == CMD_FILE_CLOSE ):
            if( self.read_file is None ):
                self.dev.send_packet( o2pkt(CMD_READ_SENSORS) )
        elif( pkt.cmd == CMD_CONFIG ):
            if( pkt.recv_cmd != 0 ):
                print( '[%s] Config Write Failed!' % self.dev.name, pkt.extra )
        #elif( pkt.cmd == CMD_DISCONNECT ):
        #    self.next_read = 0
        #    print( '[%s] Disconnected' )
        else:
            print( '[%s] Unhandled Command %d, data:' % (self.dev.name, pkt.cmd), pkt.recv_data.hex())


    def check( self ):
        if( self.next_read > 0 and time.time() >= self.next_read ):
            self.next_read = 0
            if( self.need_cfg ):
                self.dev.send_packet( o2pkt(CMD_INFO) )
                self.req_time_str = time.strftime( TIME_FORMAT )
            else:
                self.next_read = time.time() + 2.0
                self.dev.send_packet( o2pkt(CMD_READ_SENSORS) )

    def add_files( self, flist ):
        self.want_files.extend( [i for i in flist.split(',') if i] )
        if( ((self.dev.verbose or self.dev.manager.verbose) > 0) and (not self.quiet_cfg) ):
            print( '[%s] File List is now' % self.dev.name, self.want_files )

    def get_next_filename( self ):
        if( len( self.want_files ) > 0 ):
            return self.want_files.pop(0)

        return None

    def get_file( self ):
        if( self.read_file is not None ):
            return

        fname = self.get_next_filename()

        while( fname is not None ):
            ofname = fname + '.o2r'
            if( not os.path.exists(ofname) ):
                break

            if( not self.quiet_cfg ):
                print( '[%s] Already Have File %s' % (self.dev.name, ofname) )

            fname = self.get_next_filename()

        if( fname is not None ):
            self.read_file = ofname
            self.read_percent = 0
            self.read_block = self.read_want = self.read_size = 0
            if( (self.dev.verbose or self.dev.manager.verbose) > 0 ):
                ostr = '[%s] Requesting File %s, saving to %s ' % (self.dev.name, fname, ofname)
                #pad = 99 - len(ostr)
                #if( pad > 0 ):
                #    ostr += ('-' * pad) + '|'
                print( ostr )
            fname += chr(0)
            self.dev.send_packet( o2pkt(CMD_FILE_OPEN, block=self.read_block, data=fname) )
        #else:
        #    self.dev.send_packet( o2pkt(CMD_READ_SENSORS) )

    def close( self ):
        self.next_read = 0
        self.want_files = [ ]
        self.read_want = 0
        self.dev.disconnect()

    def check_settings( self ):
        check = {}
        want_o2 = 2
        if( self.args.o2_alert is not None ):
            if( self.args.o2_alert < 1 ):
                check['OxiSwitch'] = 0
            elif( self.args.o2_alert <= 100 ):
                check['CurOxiThr'] = self.args.o2_alert
                check['OxiSwitch'] = 1

        if( (self.args.hr_alert_high is not None) and (self.args.hr_alert_high < 1) ):
            check['HRSwitch'] = 0

        if( (self.args.hr_alert_low is not None) and (self.args.hr_alert_low < 1) ):
            check['HRSwitch'] = 0


        if( (self.args.hr_alert_high is not None) and (self.args.hr_alert_high > 0) and (self.args.hr_alert_high <= 200) ):
            check['HRSwitch'] = 1
            check['HRHighThr'] = self.args.hr_alert_high

        if( (self.args.hr_alert_low is not None) and (self.args.hr_alert_low > 0) and (self.args.hr_alert_low <= 200) ):
            check['HRSwitch'] = 1
            check['HRLowThr'] = self.args.hr_alert_low

        # FIXME flip low/high if reversed

        if( self.args.vibrate is not None ):
            check['CurMotor'] = self.args.vibrate

        if( self.args.screen is not None ):
            if( self.args.screen ):
                check['LightingMode'] = 2
            else:
                check['LightingMode'] = 0

        if( self.args.brightness is not None ):
            check['LightStr'] = self.args.brightness

        #if( self.args.pedtar is not None ):
        #    check['CurPedtar'] = self.args.pedtar

        update = {}

        for i in check:
            if( str(check[i]) != self.current_cfg[i] ):
                print('Updating', i, 'from', self.current_cfg[i], 'to', check[i])
                k = 'Set'
                if( i[:3] == 'Cur' ):
                    k += i[3:]
                else:
                    k += i

                update[k] = check[i]

        #print('checked:', check)
        #print('updating:', update)

        if( len(update) > 0 ):
            upstr = ''
            for i in update:
                upstr += ',"%s":"%s"' % (i, str(update[i]))
            upstr = '{' + upstr[1:] + '}'
            #print(len(upstr), upstr)
            self.dev.send_packet( o2pkt(CMD_CONFIG, data=upstr) )
            self.need_cfg = True
            self.quiet_cfg = False

