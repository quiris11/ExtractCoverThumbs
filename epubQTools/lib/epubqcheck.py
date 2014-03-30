#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of pyBookTools, licensed under GNU Affero GPLv3 or later.
# Copyright © Robert Błaut. See NOTICE for more information.
#

def QCheck(_documents, _moded, _validator):
    import zipfile
    import subprocess
    import re
    import os
    from lxml import etree

    OPFNS = {'opf': 'http://www.idpf.org/2007/opf'}
    XHTMLNS = {'xhtml': 'http://www.w3.org/1999/xhtml'}
    DCNS = {'dc': 'http://purl.org/dc/elements/1.1/'}
    NCXNS = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}
    _epubchecker_path = os.path.join(
        os.path.dirname(__file__), os.pardir, 'resources',
    	'epubcheck-3.0.1', 'epubcheck-3.0.1.jar'
    )

    if _moded:
        fe = '_moh.epub'
        nfe = '_org.epub'
    else:
        fe = '.epub'
        nfe = '_moh.epub'

    for root, dirs, files in os.walk(_documents):
        for _file in files:
            if _file.endswith(fe) and not _file.endswith(nfe):
                print('')
                print('')
                #print('************ ' + _file + ' *************')
                _epubfile = zipfile.ZipFile(os.path.join(root, _file))
                #print(_epubfile.namelist())
                for _singlefile in _epubfile.namelist():
                    if _singlefile.find('.opf') > 0:
                        #print(_singlefile)
                        if _singlefile.find(os.sep) == -1:
                            _folder = ''
                        else:
                            _folder = _singlefile.split(os.sep)[0] + os.sep
                        #print(_folder)
                        opftree = etree.fromstring(_epubfile.read(_singlefile))
                        #print etree.tostring(opftree)
                        language_tags = etree.XPath('//dc:language/text()', namespaces=DCNS)(opftree)
                        if len(language_tags) == 0:
                            print(_file.decode('utf-8') + ': No dc:language defined')
                        else:
                            if len(language_tags) > 1:
                                print(_file.decode('utf-8') + ': Multiple dc:language tags')
                            for _lang in language_tags:
                                if _lang != 'pl':
                                    print(_file.decode('utf-8') + ': Problem with dc:language. Current value: ' + _lang)

                        _metacovers = etree.XPath('//opf:meta[@name="cover"]', namespaces=OPFNS)(opftree)
                        if len(_metacovers) == 0:
                            print(_file.decode('utf-8') + ': No meta cover image defined.')
                        elif len(_metacovers) > 1:
                            print(_file.decode('utf-8') + ': Multiple meta cover images defined.')
                        else:
                            #print _metacovers[0].get('content')
                            if len(etree.XPath('//opf:item[@id="' + _metacovers[0].get('content') + '"]', namespaces=OPFNS)(opftree)) == 0:
                                print(_file.decode('utf-8') + ': Meta cover DOES NOT properly defined.')

                        _references = etree.XPath('//opf:reference', namespaces=OPFNS)(opftree)
                        _refcovcount = _reftoccount = _reftextcount = 0
                        for _reference in _references:
                            #print _reference.get('type')
                            if _reference.get('type') == 'cover':
                                _refcovcount += 1
                            if _reference.get('type') == 'toc':
                                _reftoccount += 1
                            if _reference.get('type') == 'text':
                                _reftextcount += 1

                        if _refcovcount == 0:
                            print(_file.decode('utf-8') + ': No cover guide element defined.')
                        elif _refcovcount > 1:
                            print(_file.decode('utf-8') + ': Multiple cover guide elements defined.')

                        if _reftoccount == 0:
                            print(_file.decode('utf-8') + ': No TOC guide element defined.')
                        elif _reftoccount > 1:
                            print(_file.decode('utf-8') + ': Multiple TOC guide elements defined.')

                        if _reftextcount == 0:
                            pass  # print(_file.decode('utf-8') + ': No text guide element defined.')
                        elif _reftextcount > 1:
                            print(_file.decode('utf-8') + ': Multiple text guide elements defined.')

                        _htmlfiletags = etree.XPath('//opf:item[@media-type="application/xhtml+xml"]', namespaces=OPFNS)(opftree)
                        _linkfound = _unbfound = _ufound = _wmfound = False
                        for _htmlfiletag in _htmlfiletags:
                            _htmlfilepath = _htmlfiletag.get('href')
                            #print _folder +_htmlfilepath
                            parser = etree.XMLParser(recover=True)
                            _xhtmlsoup = etree.fromstring(_epubfile.read(_folder + _htmlfilepath), parser)
                            if _wmfound is False:
                                _watermarks = etree.XPath('//*[starts-with(text(),"==")]', namespaces=XHTMLNS)(_xhtmlsoup)
                                if len(_watermarks) > 0:
                                    print(_file.decode('utf-8') + ': WM found')
                                    _wmfound = True
                            _metacharsets = etree.XPath('//xhtml:meta[@charset="utf-8"]', namespaces=XHTMLNS)(_xhtmlsoup)
                            for a in _metacharsets:
                                print etree.tostring(a)
                            _alltexts = etree.XPath('//xhtml:body//text()', namespaces=XHTMLNS)(_xhtmlsoup)
                            _alltext = ' '.join(_alltexts)
                            #print _alltext

                            if _reftoccount == 0 and _alltext.find(u'Spis treści') != -1:
                                    print(_file.decode('utf-8') + ': ################## ' + _htmlfilepath + ' #####################')
                            check_hyphs = False
                            if check_hyphs:
                                if not _ufound and _alltext.find(u'\u00AD') != -1:
                                    print(_file.decode('utf-8') + ': U+00AD hyphenate marks found.')
                                    _ufound = True
                                if not _unbfound and _alltext.find(u'\u00A0') != -1:
                                    print(_file.decode('utf-8') + ': U+00A0 non-breaking space found.')
                                    _unbfound = True
                            _links = etree.XPath('//xhtml:link', namespaces=XHTMLNS)(_xhtmlsoup)
                            for _link in _links:
                                if not _linkfound and (_link.get('type') is None):
                                    _linkfound = True
                                    print(_file.decode('utf-8') + ': At least one xhtml file has link tag without type attribute defined')

                        #Check dtb:uid - should be identical go dc:identifier
                        ncxfile = etree.XPath('//opf:item[@media-type="application/x-dtbncx+xml"]', namespaces=OPFNS)(opftree)[0].get('href')
                        ncxtree = etree.fromstring(_epubfile.read(_folder + ncxfile))
                        uniqid = etree.XPath('//opf:package', namespaces=OPFNS)(opftree)[0].get('unique-identifier')
                        if uniqid is not None:
                            try:
                                dc_identifier = etree.XPath('//dc:identifier[@id="' + uniqid + '"]/text()', namespaces=DCNS)(opftree)[0]
                            except:
                                dc_identifier = ''
                                print(_file.decode('utf-8') + ': dc:identifier with unique-id not found')
                        else:
                            print(_file.decode('utf-8') + ': no unique-identifier found')
                        try:
                            metadtd = etree.XPath('//ncx:meta[@name="dtb:uid"]', namespaces=NCXNS)(ncxtree)[0]
                            if metadtd.get('content') != dc_identifier:
                                print(_file.decode('utf-8') + ': dtd:uid and dc:identifier mismatched')
                        except IndexError:
                            print(_file.decode('utf-8') + ': dtd:uid not properly defined')

                        for meta in opftree.xpath("//opf:meta[starts-with(@name, 'calibre')]", namespaces=OPFNS):
                            print(_file.decode('utf-8') + ': calibre staff found')
                            break
                        for dcid in opftree.xpath("//dc:identifier[@opf:scheme='calibre']", namespaces={'dc': 'http://purl.org/dc/elements/1.1/', 'opf': 'http://www.idpf.org/2007/opf'}):
                            print(_file.decode('utf-8') + ': calibre staff found')
                            break

                        #print('*************************')
                        print('')
                        if _validator:
                            print('***** Validating: ' + str(_file) + ' *****')
                            subprocess.call(['java', '-jar', '%s' % _epubchecker_path, '%s' % str(os.path.join(root, _file))])
if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("directory", help="Directory with EPUB files stored")
    parser.add_argument("-m", "--mod", help="Check only _mod.epub files", action="store_true")
    parser.add_argument("-v", "--validate", help="Validate files with epubchecker", action="store_true")
    args = parser.parse_args()

    QCheck(args.directory, args.mod, args.validate)
