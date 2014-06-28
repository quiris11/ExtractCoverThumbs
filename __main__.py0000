import argparse
import os
import sys
from ExtractCoverThumbs import extract_cover_thumbs

parser = argparse.ArgumentParser()
parser.add_argument('-V', '--version', action='version',
                    version="%(prog)s (version 0.6)")
parser.add_argument("kindle_directory", help="directory where is a Kindle"
                    " Paperwhite mounted")
parser.add_argument("-v", "--verbose", help="print more informations",
                    action="store_true")
parser.add_argument("-o", "--overwrite", help="overwrite thumbnails",
                    action="store_true")
parser.add_argument("-a", "--apnx", help="also generate APNX files",
                    action="store_true")
args = parser.parse_args()

kindlepth = args.kindle_directory
docs = os.path.join(kindlepth, 'documents')

if __name__ == '__main__':
    sys.exit(extract_cover_thumbs(args.verbose, args.overwrite, args.apnx,
             kindlepth, docs))
