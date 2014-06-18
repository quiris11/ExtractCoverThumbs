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
import KindleUnpack
from apnx import APNXBuilder

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


# get_cover_image based on Pawel Jastrzebski <pawelj@vulturis.eu> work:
# https://github.com/AcidWeb/KindleButler/blob/master/KindleButler/File.py
def get_cover_image(section, mh, metadata, doctype):
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
                pdoc_cover = Image.new("L", (cover.size[0], cover.size[1]+45),
                                       "white")
                pdoc_cover.paste(cover, (0, 0))
                return pdoc_cover
            else:
                return cover
    return False


def fix_generated_thumbs(file, verbose):
    try:
        cover = Image.open(file)
    except IOError:
        return None
    try:
        dpi = cover.info["dpi"]
    except KeyError:
        if verbose:
            print('Fixing generated thumbnail "%s"...' % (file))
        pdoc_cover = Image.new("L", (cover.size[0], cover.size[1]+45), "white")
        pdoc_cover.paste(cover, (0, 0))
        return pdoc_cover
    if verbose:
        print('Generated thumbnail "%s" is fixed. DPI set up: %s. Skipping...'
              % (os.path.basename(file), dpi))
    return cover


def generate_apnx_files(dir_list, docs, verbose, overwrite):
    apnx_builder = APNXBuilder()
    for f in dir_list:
        if f.lower().endswith(('.azw3', '.mobi', '.azw')):
            mobi_path = os.path.join(docs, f)
            apnx_path = os.path.join(
                docs, os.path.splitext(f)[0] + '.sdr',
                os.path.splitext(f)[0] + '.apnx'
            )
            if not os.path.isfile(apnx_path) or args.overwrite:
                if verbose:
                    print('Generating APNX file for "%s"' % f)
                apnx_builder.write_apnx(mobi_path, apnx_path)


def main():
    if not args.verbose:
        print("START of extracting cover thumbnails...")
        print("NOTICE! AZW files are IGNORED!")
    try:
        dir_list = os.listdir(docs)
    except:
        print('* ERROR! No Kindle device found in a specified directory: ' +
              kindlepth)
        print("FINISH of extracting cover thumbnails...")
        return 0
    generate_apnx_files(dir_list, docs, args.verbose, args.overwrite)
    for f in dir_list:
        if f.lower().endswith(('.azw3', '.mobi', '.azw')):
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
            section = KindleUnpack.Sectionizer(mobi_path)
            mhlst = [KindleUnpack.MobiHeader(section, 0)]
            mh = mhlst[0]
            metadata = mh.getmetadata()
            try:
                asin = metadata['ASIN'][0]
            except KeyError:
                asin = None
            try:
                doctype = metadata['Document Type'][0]
            except KeyError:
                doctype = None
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
                cover = get_cover_image(section, mh, metadata, doctype)
                if not cover:
                    continue
                cover.save(thumbpath)
            elif args.verbose:
                print('Cover thumbnail for current file exists. Skipping...')
    thumb_dir = os.path.join(kindlepth, 'system', 'thumbnails')
    thumb_list = os.listdir(thumb_dir)
    for c in thumb_list:
        if c.startswith('thumbnail') and c.endswith('.jpg'):
            if c.endswith('portrait.jpg'):
                continue
            cover = fix_generated_thumbs(os.path.join(thumb_dir, c),
                                         args.verbose)
            if cover is not None:
                cover.save(os.path.join(thumb_dir, c), dpi=[72, 72])
    if not args.verbose:
        print("FINISH of extracting cover thumbnails...")
    return 0


if __name__ == '__main__':
    sys.exit(main())
