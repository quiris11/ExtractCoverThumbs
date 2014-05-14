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
import argparse
import sys
import os
import re
import KindleUnpack
from imghdr import what
from io import BytesIO

try:
    from PIL import Image
except ImportError:
    sys.exit('ERROR! Python Imaging Library (PIL) or Pillow not installed.')

parser = argparse.ArgumentParser()
parser.add_argument("kindle_directory", help="directory where is a Kindle"
                    " Paperwhite mounted")
parser.add_argument("-v", "--verbose", help="print more informations",
                    action="store_true")
parser.add_argument("-o", "--overwrite", help="overwrite thumbnails",
                    action="store_true")
args = parser.parse_args()

kindlepth = args.kindle_directory
docs = os.path.join(kindlepth, 'documents')


def find_header(search_id, mobi_file):
    import struct
    with open(os.path.join(mobi_file), 'rb') as f:
        content = f.read()
    exth_begin = content.find('EXTH')
    exth_header = content[exth_begin:]
    count_items, = struct.unpack('>L', exth_header[8:12])
    pos = 12
    for _ in range(count_items):
        id, size = struct.unpack('>LL', exth_header[pos:pos+8])
        exth_record = exth_header[pos + 8: pos + size]
        if id == search_id:
            return exth_record.decode('utf-8')
        pos += size


# get_cover_image based on Pawel Jastrzebski <pawelj@vulturis.eu> work:
# https://github.com/AcidWeb/KindleButler/blob/master/KindleButler/File.py
def get_cover_image(file, doctype):
    section = KindleUnpack.Sectionizer(file)
    mhlst = [KindleUnpack.MobiHeader(section, 0)]
    mh = mhlst[0]
    metadata = mh.getmetadata()
    try:
        cover_offset = metadata['CoverOffset'][0]
    except KeyError:
        print('* ERROR! Cover does NOT defined in "%s". Skipping...'
              % os.path.basename(file))
        return False
    beg = mh.firstresource
    end = section.num_sections
    imgnames = []
    for i in range(beg, end):
        data = section.load_section(i)
        tmptype = data[0:4]
        if tmptype in ["FLIS", "FCIS", "FDST", "DATP", "SRCS", "CMET",
                       "FONT", "RESC"]:
            imgnames.append(None)
            continue
        if data == chr(0xe9) + chr(0x8e) + "\r\n":
            imgnames.append(None)
            continue
        imgtype = what(None, data)
        if imgtype is None and data[0:2] == b'\xFF\xD8':
            last = len(data)
            while data[last-1:last] == b'\x00':
                last -= 1
            if data[last-2:last] == b'\xFF\xD9':
                imgtype = "jpeg"
        if imgtype is None:
            imgnames.append(None)
        else:
            imgnames.append(i)
        if len(imgnames)-1 == int(cover_offset):
            cover = Image.open(BytesIO(data))
            cover.thumbnail((220, 330), Image.ANTIALIAS)
            cover = cover.convert('L')
            if doctype == 'PDOC':
                size = cover.size
                pdoc_cover = Image.new("L", (cover.size[0], cover.size[1]+45),
                                       "white")
                pdoc_cover.paste(cover, (0, 0))
                return pdoc_cover
            else:
                return cover
    return False


def main():
    if not args.verbose:
        print("START of extracting cover thumbnails...")
    try:
        dir_list = os.listdir(docs)
    except:
        print('* ERROR! No Kindle device found in a specified directory: ' +
              kindlepth)
        print("FINISH of extracting cover thumbnails...")
        return 0
    for f in dir_list:
        if f.lower().endswith(('.azw3', '.mobi')):
            fide = f.decode(sys.getfilesystemencoding())
            mobi_path = os.path.join(docs, f)
            if args.verbose:
                try:
                    print('Processing "%s":' % fide, end=' ')
                except:
                    print('Processing %r:' % fide, end=' ')
            with open(mobi_path, 'rb') as mf:
                mobi_content = mf.read()
                if mobi_content[60:68] != 'BOOKMOBI':
                    print('* ERROR! INVALID format of file "%s". Skipping...'
                          % fide)
                    continue
            asin = find_header(113, mobi_path)
            doctype = find_header(501, mobi_path)
            if asin is None:
                print('No ASIN found in a current file. Skipping...')
                continue
            thumbpath = os.path.join(
                kindlepth, 'system', 'thumbnails',
                'thumbnail_%s_%s_portrait.jpg' % (asin, doctype)
            )
            if not os.path.isfile(thumbpath) or args.overwrite:
                if args.verbose:
                    print('No cover found for current file. Trying to fix'
                          ' it...')
                cover = get_cover_image(mobi_path, doctype)
                if not cover:
                    continue
                cover.save(thumbpath)
            elif args.verbose:
                print('Cover thumbnail for current file exists. Skipping...')
    if not args.verbose:
        print("FINISH of extracting cover thumbnails...")
    return 0


if __name__ == '__main__':
    sys.exit(main())
