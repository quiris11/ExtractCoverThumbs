#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# By Robert Blaut http://blog.blaut.biz
# This script is licensed under 
# a Creative Commons Attribution 3.0 Unported License (CC BY 3.0)
# http://creativecommons.org/licenses/by/3.0/

import os, zipfile, argparse, subprocess
from bs4 import BeautifulSoup
from os.path import expanduser
_home = expanduser("~")


parser = argparse.ArgumentParser()
parser.add_argument("directory", help="directory with EPUB files stored")
parser.add_argument("-m", "--mod", help="check only _mod.epub files", action="store_true")
parser.add_argument("-v", "--validate", help="validate files with epubchecker", action="store_true")
args = parser.parse_args()
if args.mod:
   _fileend = '_mod.epub'
else:
    _fileend = '.epub'

_documents = args.directory

####### CONFIG PARAMETR #######
_epubchecker_path = '/epubcheck-3.0.1/epubcheck-3.0.1.jar'
###############################


for root, dirs, files in os.walk(_documents):
    for _file in files:
        if _file.endswith(_fileend):
            #print('')
            #print('************ ' + _file + ' *************')
            _epubfile=zipfile.ZipFile(os.path.join(root, _file))
            #print(_epubfile.namelist())
            for _singlefile in _epubfile.namelist():
                if _singlefile.find('.opf') > 0:
                    #print(_singlefile)
                    if _singlefile.find('/') == -1:
                        _folder = ''
                    else:
                        _folder = _singlefile.split('/')[0] + '/'
                    #print(_folder)
                    _opfsoup = BeautifulSoup(_epubfile.read(_singlefile), 'lxml')
                    if len(_opfsoup('dc:language')) == 0:
                        print(_file.decode('utf-8') + ': !!!! No dc:language defined')
                    else:
                        if len(_opfsoup('dc:language')) > 1:
                            print(_file.decode('utf-8') + ': !!! Multiple dc:language tags')
                        for _lang in _opfsoup('dc:language'):
                            if _lang.get_text() != 'pl':
                                print(_file.decode('utf-8') + ': !!! Problem with dc:language. Current value: ' + _lang.get_text())
                    _metacover = _opfsoup.find('meta', {'name' : 'cover'})
                    if _metacover is None:
                        _metacover = _opfsoup.find('opf:meta', {'name' : 'cover'})
                        if _metacover is None:
                            print(_file.decode('utf-8') + ': !!! No meta cover image defined.')
                    else:
                        _id_metacover= _metacover['content']
                        if _opfsoup.find('item', {'id' : _id_metacover}) is None:
                            print(_file.decode('utf-8') + ': !!! Meta cover not properly defined.')
                    
                    if _opfsoup.find('reference', {'type' : 'cover'}) is None:
                        print(_file.decode('utf-8') + ': No cover guide element defined.')
                    else:
                        pass #print(_opfsoup.find('reference', {'type' : 'cover'}))
                    
                    if _opfsoup.find('reference', {'type' : 'toc'}) is None:
                        print(_file.decode('utf-8') + ': ! No TOC guide element defined.')
                    else:
                        pass #print(_opfsoup.find('reference', {'type' : 'toc'}))
                        
                    if _opfsoup.find('reference', {'type' : 'text'}) is None:
                        pass #print(_file.decode('utf-8') + ': No text guide element defined.')
                    else:
                        pass #print(_opfsoup.find('reference', {'type' : 'text'}))
                    def find_broken_link_tags():
                        _htmlfiletags = _opfsoup('item',{'media-type':'application/xhtml+xml'})
                        for _htmlfiletag in _htmlfiletags:
                            _htmlfilepath = _htmlfiletag['href']
                            #print _folder +_htmlfilepath
                            _xhtmlsoup = BeautifulSoup(_epubfile.read(_folder +_htmlfilepath), 'lxml')
                            for _link in _xhtmlsoup.find_all('link'):
                                if _link.get('type') is None:
                                    print(_file.decode('utf-8') + ': !!!!! At least one xhtml file has link tag without type attribute defined')
                                    return
                    find_broken_link_tags()
                    if args.validate:
                        print('')
                        print('')
                        print('***** Validating: ' + str(_file) + ' *****')
                        subprocess.call(['java', '-jar', '%s' % _epubchecker_path, '%s' % str(os.path.join(root, _file))])

