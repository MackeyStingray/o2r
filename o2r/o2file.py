import struct, os, time, datetime, csv
from collections import namedtuple

from .defines import *

class o2filereadbin:
    def __init__( self, fname ):
        self.ftype = None
        self.fname = fname

        try:
            self.fp = open( fname, 'rb' )
        except FileNotFoundError as e:
            self.fp = None
            raise

        self._parse_header()

    def __enter__( self ):
        return self

    def __exit__( self, exc_type, exc_value, exc_traceback ):
        self.close()

    def _parse_header(self):
        raw = self.fp.read(40)

        if( len(raw) < 40 ):
            raise EOFError('Failed to read binary file header')

        given_fields = 'version year month day hour minute second filesize filesize2 duration duration2 spo2_avg spo2_min spo2_3pct spo2_4pct unknown1 time_under_90pct events_under_90pct o2_score'
        calculated_fields = 'rawsize records resolution'

        self.header = namedtuple( 'ViatomBasicHeader', given_fields )._make( struct.unpack( '<HHBBBBBHHHHBBBBBHBB', raw[:26] ) )._asdict()

        if( self.header['version'] != 3 ):
            raise ImportError( 'Only Version 3 files supported (file claims to be v%d)' % self.header['version'] )

        self.ftype = 'vld' + str(self.header['version'])
        #self.header['o2_score'] /= 10
        self.header['rawsize'] = os.fstat( self.fp.fileno() ).st_size
        self.header['records'] = (self.header['rawsize'] - 40) / float(RECORD_SIZE_v3)
        self.header['resolution'] = self.header['duration'] / self.header['records']

        if( self.header['resolution'] != 2.0 and self.header['resolution'] != 4.0 ):
            raise ImportError( 'Cannot find file resolution, file probably corrupt' )

        t = time.strptime( '{year:d}-{month:02d}-{day:02d},{hour:02d}:{minute:02d}:{second:02d}'.format( **self.header ), '%Y-%m-%d,%H:%M:%S' )
        self.header['time'] = datetime.datetime( *t[:6] )
        self.header['tdelta'] = datetime.timedelta( seconds=self.header['resolution'] )

        #print( self.header )

    def read_record( self ):
        if not self.fp:
            return None

        if( not self.fp.readable() ):
            return None

        rec = self.fp.read( RECORD_SIZE_v3 )

        if( len(rec) != RECORD_SIZE_v3 ):
            return None

        rec = namedtuple( 'ViatomRecord', 'spo2 heartrate oximetry_invalid motion vibration' )._make( struct.unpack( '<BB?BB', rec ) )._asdict()

        if( rec['spo2'] < 10 or rec['spo2'] > 100 ):
            rec['oximetry_invalid'] = True

        rec['time'] = self.header['time'].strftime( CSV_TIMEFMT )
        self.header['time'] += self.header['tdelta']

        return rec

    def records( self ):
        rec = self.read_record()

        while rec:
            yield rec
            rec = self.read_record()

    def close( self ):
        if( self.fp ):
            self.fp.close()
            self.fp = None



class o2filereadcsv:
    def __init__( self, fname ):
        self.ftype = 'csv'
        self.fname = fname

        raise NotImplementedError()

        try:
            self.fp = open( fname, 'rb' )
        except:
            self.fp = None
            raise

        self._parse_header()

    def __enter__( self ):
        return self

    def __exit__( self, exc_type, exc_value, exc_traceback ):
        self.close()

    def _parse_header(self):
        raise NotImplementedError()
        raw = self.fp.read(40)

    def records( self ):
        raise NotImplementedError()

    def close( self ):
        if( self.fp ):
            self.fp.close()
            self.fp = None


def o2fileread( fname ):
    fp = open( fname, 'rb' )
    ver = fp.read( 2 )
    fp.close()

    if( ver == b'\x03\x00' ):
        #print('bin')
        return o2filereadbin( fname )

    if( fname[-4:] == '.csv' ):
        #print('csv')
        return o2filereadcsv( fname )

    # FIXME try harder to detect CSV?
    return None


class o2filewritecsv:
    def __init__( self, fname ):
        self.ftype = 'csv'
        self.fname = fname

        self.fp = open( fname, 'w' )

        self.csvout = csv.DictWriter( self.fp, fieldnames=CSV_FIELDS, restval='', extrasaction='ignore', quoting=csv.QUOTE_MINIMAL )
        self.csvout.writerow( CSV_TITLES )

    def writerow( self, data ):
        #self.csvout.writerow( [ data[x] for x in CSV_FIELDS ] + [''] )
        self.csvout.writerow( data )

    def close( self ):
        if( self.fp ):
            self.fp.close()
            self.fp = None

class o2filewritebin:
    def __init__( self, fname ):
        self.ftype = 'vld3'
        self.fname = fname

        raise NotImplementedError()

        self.fp = open( fname, 'w' )

    def writerow( self, data ):
        self.csvout.writerow( data )

    def close( self ):
        if( self.fp ):
            self.fp.close()
            self.fp = None


def o2filewrite( fname, ftype ):
    if( ftype == 'csv' ):
        return o2filewritecsv( fname )

    return o2filewritebin( fname )



