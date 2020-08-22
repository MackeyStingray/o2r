import o2r
import csv, argparse, os

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="O2Ring Data Converter", epilog='If neither --csv nor --bin are provided it will attempt to auto-detect and convert to the opposite' )
    arg_parser.add_argument( '--csv', help='Assume input files are binary and convert them to CSV', action="store_true" )
    arg_parser.add_argument( '--bin', help='Assume input files are CSV and convert them to binary', action="store_true" )
    arg_parser.add_argument( '--force', help='Overwrite output file if it exists', action="store_true" )
    arg_parser.add_argument( 'file', help='File(s) to convert', action='append', nargs='+' )
    args = arg_parser.parse_args()

    #print(args)

    if( (not args.csv) and (not args.bin) ):
        pass

    for fname in args.file[0]:
        infile = o2r.o2fileread( fname )

        if( args.csv ):
            oftype = 'csv'
        elif( args.bin ):
            oftype = 'vld'
        else:
            if( infile.ftype == 'csv' ):
                oftype = 'vld'
            else:
                oftype = 'csv'

        if( fname[-4] == '.' ):
            outname = fname[:-3] + oftype
        else:
            outname = fname + '.' + oftype

        if( (not args.force) and os.path.exists( outname ) ):
            print( 'Skipping %s: output file %s already exists' % (fname, outname) )
            continue

        outfile = o2r.o2filewrite( outname, oftype )

        print( 'Converting %s (type: %s) to %s (type: %s)' % (fname, infile.ftype, outname, outfile.ftype) )

        for rec in infile.records():
            outfile.writerow( rec )

        infile.close()
        outfile.close()

