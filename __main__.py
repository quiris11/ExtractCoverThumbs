#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of ExtractCoverThumbs, licensed under
# GNU Affero GPLv3 or later.
# Copyright © Robert Błaut. See NOTICE for more information.
#
# This is script extracts missing Cover Thumbnails from eBooks downloaded
# from Amazon Personal Documents Service and side loads them
# to your Kindle Paperwhite.
#

from __future__ import print_function

__license__ = 'GNU Affero GPL v3'
__copyright__ = '2014, Robert Błaut listy@blaut.biz'
__appname__ = u'ExtractCoverThumbs'
numeric_version = (0, 8)
__version__ = u'.'.join(map(unicode, numeric_version))
__author__ = u'Robert Błaut <listy@blaut.biz>'

import argparse
import os
import sys
from ExtractCoverThumbs import extract_cover_thumbs
from distutils.util import strtobool

parser = argparse.ArgumentParser()
parser.add_argument('-V', '--version', action='version',
                    version="%(prog)s (version " + __version__ + ")")
parser.add_argument("kindle_directory", help="directory where is a Kindle"
                    " Paperwhite mounted")
parser.add_argument("-v", "--verbose", help="print more informations",
                    action="store_true")
parser.add_argument("--overwrite-thumbs", help="overwrite cover thumbnails",
                    action="store_true")
parser.add_argument("--overwrite-apnx", help="overwrite APNX files",
                    action="store_true")
parser.add_argument("-s", "--skip-apnx", help="skip generating APNX files",
                    action="store_true")
parser.add_argument("-z", "--azw", help="also extract covers from AZW files",
                    action="store_true")
parser.add_argument('-d', '--days', nargs='?', metavar='DAYS', const='7',
                    help='only "younger" ebooks than specified DAYS will '
                    'be processed (default: 7 days).')
args = parser.parse_args()

kindlepth = args.kindle_directory
docs = os.path.join(kindlepth, 'documents')


def user_yes_no_query(question):
    sys.stdout.write('%s [y/n]\n' % question)
    while True:
        try:
            return strtobool(raw_input().lower())
        except ValueError:
            sys.stdout.write('Please respond with \'y\' or \'n\'.\n')

if __name__ == '__main__':
    extract_cover_thumbs(args.verbose, args.overwrite_thumbs,
                         args.overwrite_apnx, args.skip_apnx,
                         kindlepth, docs, args.azw, args.days)
    if sys.platform == 'darwin':
        ans_ok = user_yes_no_query('Eject Kindle?')
        if ans_ok:
            os.system('diskutil eject ' + kindlepth)
