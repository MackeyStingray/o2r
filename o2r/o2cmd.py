from .defines import *
from .o2pkt import o2pkt
import time

class o2cmd:
    def SetTime( ):
        cmd = '{"SetTIME":"%s"}' % time.strftime( TIME_FORMAT )
        return o2pkt(CMD_CONFIG, data=cmd)

    def SetConfig( cfg ):
        if( len(cfg) < 1 ):
            return None

        upstr = ''
        for i in cfg:
            upstr += ',"%s":"%s"' % (i, str(cfg[i]))
        upstr = '{' + upstr[1:] + '}'
        #print(len(upstr), upstr)
        return o2pkt(CMD_CONFIG, data=upstr)







