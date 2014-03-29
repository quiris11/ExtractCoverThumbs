#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of pyBookTools, licensed under GNU Affero GPLv3 or later.
# Copyright © Robert Błaut. See NOTICE for more information.
#
# This is script extracts missing Cover Thumbnails from eBooks downloaded 
# from Amazon Personal Documents Service and side loads them to your Kindle Paperwhite.
# 
# 1. You have to properly set up _kindle_path variable to path where is Your Paperwhite mounted.

import sys, os, re, shutil, subprocess, tempfile

########## CONFIG VARIABLE ############
_kindle_path = '/Volumes/Kindle' 			# for example 'E:', '/Volumes/Kindle'
####### END OF CONFIG VARIABLES ########

_kindle_unpack = os.path.join(os.getcwd(), 'KindleUnpack_v62', 'lib', 'kindleunpack.py')
_documents = os.path.join(_kindle_path, 'documents')

try:
	_dir_content = os.listdir(_documents)
except:
	sys.exit('No Kindle device found in a specified path: _kindle_path. Giving up…')
for _file in _dir_content:
	if _file.endswith('.azw3') or _file.endswith('.azw'):
		print('Processing file ' + _file + '...')
		try:
			_asin = re.search('.+_(.+?)\..+', _file)
			_asin_found = _asin.group(1)	
		except:
			print('No ASIN found in a current file. Let me try another one…')
			continue
		if not os.path.isfile(os.path.join(_kindle_path, 'system', 'thumbnails', 'thumbnail_' + _asin_found + '_PDOC_portrait.jpg')) and not os.path.isfile(os.path.join(_kindle_path, 'system', 'thumbnails', 'thumbnail_' + _asin.group(1) + '_EBOK_portrait.jpg')):
			print('No cover found…')
			_tempdir = tempfile.mkdtemp()
			with open(os.devnull, 'wb') as devnull:
				try:
					subprocess.check_call(['python', _kindle_unpack, os.path.join(_documents, _file), _tempdir], stdout=devnull, stderr=subprocess.STDOUT)
				except:
					sys.exit('No KindleUnpack Tool found in a specified path: _kindle_unpack_path. Giving up…')
			if _file.endswith('.azw3'):
				_opf_dir = os.path.join(_tempdir, 'mobi8', 'OEBPS')
			else:
				_opf_dir = os.path.join(_tempdir, 'mobi7')
			for _opf in os.listdir(_opf_dir):
				if _opf.endswith('.opf'):
					with open(os.path.join(_opf_dir, _opf), 'r') as f:
						_opf_content = f.read()
						_thumb_file = re.search('.+id="cover_img.+href="(.+)\/(.+)".+', _opf_content)
						if _thumb_file:
							shutil.move(os.path.join(_tempdir, 'mobi7', _thumb_file.group(1), _thumb_file.group(2)), os.path.join(_kindle_path, 'system', 'thumbnails', 'thumbnail_' + _asin.group(1) + '_PDOC_portrait.jpg'))
							print('Cover copied to your device…')
			if os.path.isdir(_tempdir):
				shutil.rmtree(_tempdir)