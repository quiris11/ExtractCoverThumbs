#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# By Robert Blaut http://blog.blaut.biz
# This script is licensed under 
# a Creative Commons Attribution 3.0 Unported License (CC BY 3.0)
# http://creativecommons.org/licenses/by/3.0/
#
# This is script extracts missing Cover Thumbnails from eBooks downloaded 
# from Amazon Personal Documents Service and side loads them to your Kindle Paperwhite.
# 
# 1. You have to download and install KindleUnpack tool and configure _kindle_unpack_path variable below.
# 2. You also have to properly set up _kindle_path variable to path where is Your Paperwhite mounted.

import os, re, shutil, subprocess, tempfile

########## CONFIG VARIABLES ############
_kindle_unpack_path = '/KindleUnpack_v62'
_kindle_path = '/Volumes/Kindle' 			# for example 'E:', '/Volumes/Kindle'
####### END OF CONFIG VARIABLES ########

_kindle_unpack_pathall = os.path.join(_kindle_unpack_path, 'lib', 'kindleunpack.py')
_documents = os.path.join(_kindle_path, 'documents')

for _file in os.listdir(_documents):
	if _file.endswith('.azw3') or _file.endswith('.azw'):
		print 'Processing file ' + _file + '...'
		_asin = re.search('.+_(.+?)\..+', _file)
		if not os.path.isfile(os.path.join(_kindle_path, 'system', 'thumbnails', 'thumbnail_' + _asin.group(1) + '_PDOC_portrait.jpg')) and not os.path.isfile(os.path.join(_kindle_path, 'system', 'thumbnails', 'thumbnail_' + _asin.group(1) + '_EBOK_portrait.jpg')):
			print 'No cover found…'
			_tempdir = tempfile.mkdtemp()
			with open(os.devnull, 'wb') as devnull:
				subprocess.check_call(['python', _kindle_unpack_pathall, os.path.join(_documents, _file), _tempdir], stdout=devnull, stderr=subprocess.STDOUT)
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
							print 'Cover copied to your device…'
			if os.path.isdir(_tempdir):
				shutil.rmtree(_tempdir)