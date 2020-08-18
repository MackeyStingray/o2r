import struct
#import binascii

from .defines import *

class o2pkt:
    
    def __init__(self, cmd, block=0, data=None):
        self.cmd = cmd
        self.block = block
        self.extra = data
        self.recv_buf = ""
        self.recv_want = None
        self.recv_cmd = None
        self.recv_block = 0
        self.recv_crc = 0
        self.recv_data = b""

    def packetify( self ):
        out = struct.pack( '<BBBHH', 0xAA, self.cmd, (self.cmd ^ 0xFF), self.block, len(self.extra or "") )

        if self.extra:
            out += bytes(self.extra, 'utf-8')

        out += struct.pack( '<B', self.chksum(out) )
        #print(binascii.hexlify(out))
        return out

    def recv( self, data ):
        if self.recv_want is None:
            if( len(data) < 8 ):
                raise EOFError("Receive didn't return enough data")

            (src, self.recv_cmd, ncmd, self.recv_block, self.recv_want) = struct.unpack( '<BBBHH', data[:7] )

            if( src != 0x55 ):
                raise TypeError("Packet not from ring")

            if( self.recv_cmd != (ncmd ^ 0xFF) ):
                raise KeyError("Command Check Failed")

            self.recv_buf = data
            self.recv_want += 8
        else:
            self.recv_buf += data

        if( len(self.recv_buf) < self.recv_want ):
            #print('want', self.recv_want, 'have', len(self.recv_buf))
            return False

        if( len(self.recv_buf) != self.recv_want ):
            raise BufferError("Got more data than expected")

        if( self.chksum(self.recv_buf[:-1]) != self.recv_buf[-1] ):
            raise ValueError("Checksum Failed! want %02X got %02X" % (self.recv_buf[-1], self.recv_crc))

        self.recv_data = self.recv_buf[7:-1]
        return True # self.recv_buf[:-1]

    # Standard CRC-8-CCITT checksum with 0x07 polynomial and 0x00 seed
    #  below function uses a hybrid method instead of a lookup table or bit shifting
    def _crc_byte( self, b ):
        chk = self.recv_crc ^ b
        self.recv_crc = 0

        # XOR values calculated for 0x01 0x02 0x04 0x08 0x10 0x20 0x40 0x80
        if chk & 0x01: self.recv_crc = 0x07
        if chk & 0x02: self.recv_crc ^= 0x0e
        if chk & 0x04: self.recv_crc ^= 0x1c
        if chk & 0x08: self.recv_crc ^= 0x38
        if chk & 0x10: self.recv_crc ^= 0x70
        if chk & 0x20: self.recv_crc ^= 0xe0
        if chk & 0x40: self.recv_crc ^= 0xc7
        if chk & 0x80: self.recv_crc ^= 0x89

    def chksum( self, data ):
        self.recv_crc = 0

        for i in data:
            self._crc_byte( i )

        return self.recv_crc
