from .defines import *
from .o2pkt import o2pkt
import time

class o2cmd:
    def SetTime( ):
        cmd = '{"SetTIME":"%s"}' % time.strftime( TIME_FORMAT )
        return o2pkt(CMD_CONFIG, data=cmd)










