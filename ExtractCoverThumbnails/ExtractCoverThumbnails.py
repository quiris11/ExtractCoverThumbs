#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of pyBookTools, licensed under GNU Affero GPLv3 or later.
# Copyright © Robert Błaut. See NOTICE for more information.
#
# This is script extracts missing Cover Thumbnails from eBooks downloaded
# from Amazon Personal Documents Service and side loads them
# to your Kindle Paperwhite.
#

import argparse
import sys
import os
import re
import shutil
import tempfile

sys.path.append(os.path.join(os.path.dirname(__file__), 'KindleUnpack_v64',
                'lib'))
import kindleunpack

parser = argparse.ArgumentParser()
parser.add_argument("kindle_directory", help="directory where is a Kindle"
                    " Paperwhite mounted")
args = parser.parse_args()

_kindle_path = args.kindle_directory
_kindle_unpack = os.path.join(os.getcwd(), 'KindleUnpack_v64',
                              'lib', 'kindleunpack.py')
_documents = os.path.join(_kindle_path, 'documents')


class NullDevice():
    def write(self, s):
        pass


try:
    _dir_content = os.listdir(_documents)
except:
    sys.exit('No Kindle device found in a specified directory'
             ': ' + _kindle_path)
for _file in _dir_content:
    if _file.endswith('.azw3') or _file.endswith('.azw'):
        print('')
        print('Processing file ' + _file + '...')
        try:
            _asin = re.search('.+_(.+?)\..+', _file)
            _asin_found = _asin.group(1)
        except:
            print('No ASIN found in a current file. Skipping...')
            continue
        if not os.path.isfile(os.path.join(
            _kindle_path, 'system', 'thumbnails',
            'thumbnail_' + _asin_found + '_PDOC_portrait.jpg'
        )) and not os.path.isfile(os.path.join(
            _kindle_path, 'system', 'thumbnails',
            'thumbnail_' + _asin.group(1) + '_EBOK_portrait.jpg'
        )):
            print("No cover found for current file. Trying to fix it...")
            _tempdir = tempfile.mkdtemp()
            original_stdout = sys.stdout  # keep a reference to STDOUT
            sys.stdout = NullDevice()  # redirect the real STDOUT
            with open(os.devnull, 'wb') as devnull:
                kindleunpack.unpackBook(os.path.join(_documents, _file),
                                        _tempdir)
            sys.stdout = original_stdout  # turn STDOUT back on
            if _file.endswith('.azw3'):
                _opf_dir = os.path.join(_tempdir, 'mobi8', 'OEBPS')
            else:
                _opf_dir = os.path.join(_tempdir, 'mobi7')
            for _opf in os.listdir(_opf_dir):
                if _opf.endswith('.opf'):
                    with open(os.path.join(_opf_dir, _opf), 'r') as f:
                        _opf_content = f.read()
                        _thumb_file = re.search(
                            '.+properties="cover-image".+href="(.+)\/(.+)".+',
                            _opf_content
                        )
                        if _thumb_file:
                            shutil.move(os.path.join(
                                _tempdir, 'mobi7', _thumb_file.group(1),
                                _thumb_file.group(2)),
                                os.path.join(
                                    _kindle_path, 'system', 'thumbnails',
                                    'thumbnail_' + _asin.group(1) + '_PDOC'
                                    '_portrait.jpg'
                                )
                            )
                            print('Cover thumbnail copied to your device...')
                        else:
                            print('Cover image not found. Skipping...')
            if os.path.isdir(_tempdir):
                shutil.rmtree(_tempdir)
        else:
            print('Cover thumbnail for current file exists. Skipping...')
