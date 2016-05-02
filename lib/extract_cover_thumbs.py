#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of ExtractCoverThumbs, licensed under
# GNU Affero GPLv3 or later.
# Copyright © Robert Błaut. See NOTICE for more information.
#
# This script extracts missing Cover Thumbnails from eBooks downloaded
# from Amazon Personal Documents Service and side loads them
# to your Kindle Paperwhite.
#

from __future__ import print_function
import sys
import os
import csv
import shutil
import tempfile

from imghdr import what
from io import BytesIO
from datetime import datetime

import kindle_unpack
from lib.apnx import APNXBuilder
from lib.pages import find_exth
from lib.pages import get_pages
from lib.get_real_pages import get_real_pages

try:
    from PIL import Image
except ImportError:
    sys.exit('ERROR! Python Imaging Library (PIL) or Pillow not installed.')


def clean_temp(sourcedir):
    for p in os.listdir(os.path.join(sourcedir, os.pardir)):
            if 'epubQTools-tmp-' in p:
                if os.path.isdir(os.path.join(sourcedir, os.pardir, p)):
                    try:
                        shutil.rmtree(os.path.join(sourcedir, os.pardir, p))
                    except:
                        if sys.platform == 'win32':
                            os.system('rmdir /S /Q \"{}\"'.format(
                                os.path.join(sourcedir, os.pardir, p)
                            ))
                        else:
                            raise


def asin_list_from_csv(mf):
    if os.path.isfile(mf):
        with open(mf) as f:
            csvread = csv.reader(f, delimiter=';', quotechar='"',
                                 quoting=csv.QUOTE_ALL)
            return [row[0] for row in csvread]
    else:
        with open(mf, 'wb') as o:
            csvwrite = csv.writer(o, delimiter=';', quotechar='"',
                                  quoting=csv.QUOTE_ALL)
            csvwrite.writerow(
                ['asin', 'lang', 'author', 'title', 'pages', 'is_real']
            )
            return []


def dump_pages(asinlist, mf, dirpath, fil):
    row = get_pages(dirpath, fil)
    if row[0] in asinlist or row is None:
        return
    with open(mf, 'ab') as o:
        print('* Updating book pages CSV file...')
        csvwrite = csv.writer(o, delimiter=';', quotechar='"',
                              quoting=csv.QUOTE_ALL)
        csvwrite.writerow(row)


# get_cover_image based on Pawel Jastrzebski <pawelj@vulturis.eu> work:
# https://github.com/AcidWeb/KindleButler/blob/master/KindleButler/File.py
def get_cover_image(section, mh, metadata, doctype, file, fide, is_verbose,
                    fix_thumb):
    try:
        cover_offset = metadata['CoverOffset'][0]
    except KeyError:
        print('ERROR! No cover found in "%s"' % fide)
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
            while data[last - 1:last] == b'\x00':
                last -= 1
            if data[last - 2:last] == b'\xFF\xD9':
                imgtype = "jpeg"
        if imgtype is None:
            imgnames.append(None)
        else:
            imgnames.append(i)
        if len(imgnames) - 1 == int(cover_offset):
            cover = Image.open(BytesIO(data))
            if fix_thumb:
                cover.thumbnail((283, 415), Image.ANTIALIAS)
            else:
                cover.thumbnail((305, 470), Image.ANTIALIAS)
            cover = cover.convert('L')
            if doctype == 'PDOC' and fix_thumb:
                pdoc_cover = Image.new(
                    "L",
                    (cover.size[0], cover.size[1] + 55),
                    "white"
                )
                pdoc_cover.paste(cover, (0, 0))
                if is_verbose:
                    print('DONE!')
                return pdoc_cover
            else:
                if is_verbose:
                    print('DONE!')
                return cover
    return False


def fix_generated_thumbs(file, is_verbose, fix_thumb):
    try:
        cover = Image.open(file)
    except IOError:
        return False
    try:
        dpi = cover.info["dpi"]
    except KeyError:
        dpi = (96, 96)
    if dpi == (96, 96) and fix_thumb:
        if is_verbose:
            print('* Fixing generated thumbnail "%s"...' % (file))
        pdoc_cover = Image.new("L", (cover.size[0], cover.size[1] + 45),
                               "white")
        pdoc_cover.paste(cover, (0, 0))
        pdoc_cover.save(file, dpi=[72, 72])
    elif dpi == (72, 72) and not fix_thumb:
        if is_verbose:
            print('* Reverse fix for generated thumbnail "%s"...' % (file))
        pdoc_cover = Image.new("L", (cover.size[0], cover.size[1] - 45),
                               "white")
        pdoc_cover.paste(cover, (0, 0))
        pdoc_cover.save(file, dpi=[96, 96])
    else:
        if is_verbose:
            print('* Generated thumbnail "%s" is OK. DPI: %s. Skipping...'
                  % (os.path.basename(file), dpi))
    return False


def generate_apnx_files(dir_list, docs, is_verbose, is_overwrite_apnx, days,
                        tempdir):
    apnx_builder = APNXBuilder()
    if days is not None:
        dtt = datetime.today()
        days_int = int(days)
    else:
        days_int = 0
        diff = 0
    for f in dir_list:
        if days is not None:
            dt = os.path.getctime(os.path.join(docs, f))
            dt = datetime.fromtimestamp(dt).strftime('%Y-%m-%d')
            dt = datetime.strptime(dt, '%Y-%m-%d')
            diff = (dtt - dt).days
        if f.lower().endswith(('.azw3', '.mobi', '.azw')) and diff <= days_int:
            mobi_path = os.path.join(docs, f)
            if os.path.isdir(os.path.join(docs,
                                          os.path.splitext(f)[0] + '.sdr')):
                apnx_path = os.path.join(
                    docs, os.path.splitext(f)[0] + '.sdr',
                    os.path.splitext(f)[0] + '.apnx'
                )
            else:
                apnx_path = os.path.join(
                    docs, os.path.splitext(f)[0] + '.apnx'
                )
            if not os.path.isfile(apnx_path) or is_overwrite_apnx:
                if is_verbose:
                    print('* Generating APNX file for "%s"'
                          % f.decode(sys.getfilesystemencoding()))
                    if os.path.isfile(os.path.join(
                            tempdir, 'extract_cover_thumbs-book-pages.csv')):
                        with open(os.path.join(
                                tempdir, 'extract_cover_thumbs-book-pages.csv'
                        ), 'rb') as f:
                            csvread = csv.reader(
                                f, delimiter=';', quotechar='"',
                                quoting=csv.QUOTE_ALL
                            )
                            with open(mobi_path, 'rb') as f:
                                mobi_content = f.read()
                            if mobi_content[60:68] != 'BOOKMOBI':
                                print('* Invalid file format. Skipping...')
                                asin = ''
                            else:
                                asin = find_exth(113, mobi_content)
                            found = False
                            for i in csvread:
                                if i[0] == asin:
                                    print(
                                        '  * Using %s pages defined '
                                        'in extract_cover_thumbs-book-pages'
                                        '.csv' % (i[4]))
                                    apnx_builder.write_apnx(
                                        mobi_path, apnx_path, int(i[4])
                                    )
                                    found = True
                                    continue
                            if not found:
                                print(
                                    '  ! Book not found in '
                                    'extract_cover_thumbs-book-pages.csv.'
                                    ' Fast algorithm used...')
                                apnx_builder.write_apnx(mobi_path, apnx_path)

                    else:
                        apnx_builder.write_apnx(mobi_path, apnx_path)


def extract_cover_thumbs(is_silent, is_overwrite_pdoc_thumbs,
                         is_overwrite_amzn_thumbs, is_overwrite_apnx,
                         skip_apnx, kindlepath, is_azw, days, fix_thumb,
                         lubimy_czytac):
    docs = os.path.join(kindlepath, 'documents')
    is_verbose = not is_silent
    try:
        dir_list = os.listdir(docs)
        dir_list.sort()
    except:
        print('* ERROR! No Kindle device found in a specified directory: ' +
              kindlepath)
        return 1
    if days is not None:
        dtt = datetime.today()
        days_int = int(days)
        print('Notice! Processing files not older than ' + days + ' days.')
    else:
        days_int = 0
        diff = 0

    # move CSV file to computer temp dir to speed up updating process
    tempdir = tempfile.mkdtemp(suffix='', prefix='extract_cover_thumbs-tmp-')
    csv_pages_name = 'extract_cover_thumbs-book-pages.csv'
    csv_pages = os.path.join(tempdir, csv_pages_name)
    if os.path.isfile(os.path.join(docs, csv_pages_name)):
        shutil.copy2(os.path.join(docs, csv_pages_name),
                     os.path.join(tempdir, csv_pages_name))

    # load ASIN list from CSV
    asinlist = asin_list_from_csv(csv_pages)

    if not os.path.isdir(os.path.join(kindlepath, 'system', 'thumbnails')):
        print('* ERROR! No Kindle device found in the specified path: "' +
              os.path.join(kindlepath) + '"')
        return 1
    print("START of extracting cover thumbnails...")
    if is_azw:
        extensions = ('.azw', '.azw3', '.mobi')
    else:
        extensions = ('.azw3', '.mobi')
    for f in dir_list:
        if days is not None:
            dt = os.path.getctime(os.path.join(docs, f))
            dt = datetime.fromtimestamp(dt).strftime('%Y-%m-%d')
            dt = datetime.strptime(dt, '%Y-%m-%d')
            diff = (dtt - dt).days
        if f.lower().endswith(extensions) and diff <= days_int:
            fide = f.decode(sys.getfilesystemencoding())
            mobi_path = os.path.join(docs, f)
            dump_pages(asinlist, csv_pages, docs, f)
            if is_verbose:
                try:
                    print('* %s:' % fide, end=' ')
                except:
                    print('* %r:' % fide, end=' ')
            with open(mobi_path, 'rb') as mf:
                mobi_content = mf.read()
                if mobi_content[60:68] != 'BOOKMOBI':
                    print('* Not a valid MOBI file "%s".'
                          % fide)
                    continue
            section = kindle_unpack.Sectionizer(mobi_path)
            mhlst = [kindle_unpack.MobiHeader(section, 0)]
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
                print('ERROR! No ASIN found in "%s"' % fide)
                continue
            thumbpath = os.path.join(
                kindlepath, 'system', 'thumbnails',
                'thumbnail_%s_%s_portrait.jpg' % (asin, doctype)
            )
            if (not os.path.isfile(thumbpath) or
                    (is_overwrite_pdoc_thumbs and doctype == 'PDOC') or
                    (is_overwrite_amzn_thumbs and (
                        doctype == 'EBOK' or doctype == 'EBSP'
                    ))):
                if is_verbose:
                    print('EXTRACTING COVER:', end=' ')
                try:
                    cover = get_cover_image(section, mh, metadata, doctype, f,
                                            fide, is_verbose, fix_thumb)
                except IOError:
                    print('FAILED! Image format unrecognized...')
                    continue
                if not cover:
                    continue
                cover.save(thumbpath)
            elif is_verbose:
                print('skipped (cover present or overwriting not forced).')
    if lubimy_czytac and days:
        print("START of downloading real book page numbers...")
        get_real_pages(os.path.join(
            tempdir, 'extract_cover_thumbs-book-pages.csv'))
        print("FINISH of downloading real book page numbers...")
    if not skip_apnx:
        print("START of generating book page numbers (APNX files)...")
        generate_apnx_files(dir_list, docs, is_verbose, is_overwrite_apnx,
                            days, tempdir)
        print("FINISH of generating book page numbers (APNX files)...")

    if is_overwrite_pdoc_thumbs:
        thumb_dir = os.path.join(kindlepath, 'system', 'thumbnails')
        thumb_list = os.listdir(thumb_dir)
        for c in thumb_list:
            if c.startswith('thumbnail') and c.endswith('.jpg'):
                if c.endswith('portrait.jpg'):
                    continue
                fix_generated_thumbs(os.path.join(thumb_dir, c),
                                     is_verbose, fix_thumb)
    print("FINISH of extracting cover thumbnails...")
    shutil.copy2(os.path.join(tempdir, csv_pages_name),
                 os.path.join(docs, csv_pages_name))
    clean_temp(tempdir)
    return 0
