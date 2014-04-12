#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of pyBookTools, licensed under GNU Affero GPLv3 or later.
# Copyright © Robert Błaut. See NOTICE for more information.
#

import zipfile
import subprocess
import re
import os
import sys
from lxml import etree

OPFNS = {'opf': 'http://www.idpf.org/2007/opf'}
XHTMLNS = {'xhtml': 'http://www.w3.org/1999/xhtml'}
DCNS = {'dc': 'http://purl.org/dc/elements/1.1/'}
NCXNS = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}
SVGNS = {'svg': 'http://www.w3.org/2000/svg'}


def check_meta_html_covers(tree, dir, epub, file_dec):
    html_cover_path = etree.XPath('//opf:reference[@type="cover"]',
                                  namespaces=OPFNS)(tree)[0].get('href')
    try:
        meta_cover_id = etree.XPath('//opf:meta[@name="cover"]',
                                    namespaces=OPFNS)(tree)[0].get('content')
    except IndexError:
        print(file_dec + ': No meta cover image defined.')
        return 0
    try:
        meta_cover_path = etree.XPath(
            '//opf:item[@id="' + meta_cover_id + '"]',
            namespaces=OPFNS
        )(tree)[0].get('href')
    except IndexError:
        print(file_dec + ': Meta cover does not properly defined.')
        return 0
    parser = etree.XMLParser(recover=True)
    html_cover_tree = etree.fromstring(
        epub.read(dir + html_cover_path), parser
    )
    if html_cover_tree is None:
        print 'Error loading HTML cover... Probably not a html file...'
        return 0
    allimgs = etree.XPath('//xhtml:img', namespaces=XHTMLNS)(html_cover_tree)
    if len(allimgs) > 1:
        print file_dec + ': Too many cover images...'
    for img in allimgs:
        if img.get('src').find(meta_cover_path) == -1:
            print(file_dec + ': Meta cover and HTML cover mismatched.')
    allsvgimgs = etree.XPath('//svg:image', namespaces=SVGNS)(html_cover_tree)
    if len(allimgs) > 1:
        print file_dec + ': Too many cover images...'
    for svgimg in allsvgimgs:
        if svgimg.get('{http://www.w3.org/1999/xlink}href').find(
                meta_cover_path
        ) == -1:
            print(file_dec + ': Meta cover and HTML cover mismatched.')


def find_cover_image(_opftree, _file_dec):
    images = etree.XPath('//opf:item[@media-type="image/jpeg"]',
                         namespaces=OPFNS)(_opftree)
    cover_found = 0
    if len(images) != 0:
        for imag in images:
            img_href_lower = imag.get('href').lower()
            if (img_href_lower.find('cover') != -1 or
                    img_href_lower.find('okladka') != -1):
                cover_found = 1
                print(_file_dec + ': Candidate image for cover found:' +
                      ' href=' + imag.get('href') +
                      ' id=' + imag.get('id'))
                break
        if cover_found == 0:
            print(_file_dec + ': No candidate cover images found. '
                  'Check a list of all images:')
            for imag in images:
                print imag.get('href')
    else:
        print(_file_dec + ': No images in an entire book found...')


def qcheck_single_file(_singlefile, _epubfile, _file_dec):
    if _singlefile.find('/') == -1:
        _folder = ''
    else:
        _folder = _singlefile.split('/')[0] + '/'
    opftree = etree.fromstring(_epubfile.read(_singlefile))
    language_tags = etree.XPath('//dc:language/text()',
                                namespaces=DCNS)(opftree)
    if len(language_tags) == 0:
        print(_file_dec + ': No dc:language defined')
    else:
        if len(language_tags) > 1:
            print(_file_dec + ': Multiple dc:language tags')
        for _lang in language_tags:
            if _lang != 'pl':
                print(_file_dec + ': Problem with '
                      'dc:language. Current value: ' + _lang)

    _metacovers = etree.XPath('//opf:meta[@name="cover"]',
                              namespaces=OPFNS)(opftree)
    if len(_metacovers) > 1:
        print(_file_dec + ': Multiple meta cover images defined.')

    _references = etree.XPath('//opf:reference', namespaces=OPFNS)(opftree)
    _refcovcount = _reftoccount = _reftextcount = 0
    for _reference in _references:
        if _reference.get('type') == 'cover':
            _refcovcount += 1
        if _reference.get('type') == 'toc':
            _reftoccount += 1
        if _reference.get('type') == 'text':
            _reftextcount += 1

    if _refcovcount == 0:
        print(_file_dec + ': No cover guide element defined.')
    elif _refcovcount > 1:
        print(_file_dec + ': Multiple cover guide elements defined.')

    if _reftoccount == 0:
        print(_file_dec + ': No TOC guide element defined.')
    elif _reftoccount > 1:
        print(_file_dec + ': Multiple TOC guide elements defined.')

    if _reftextcount == 0:
        pass  # print(_file_dec + ': No text guide element defined.')
    elif _reftextcount > 1:
        print(_file_dec + ': Multiple text guide elements defined.')

    if len(_metacovers) == 0 and _refcovcount == 0:
        find_cover_image(opftree, _file_dec)

    if _refcovcount == 1 and len(_metacovers) == 1:
        check_meta_html_covers(opftree, _folder, _epubfile, _file_dec)

    _htmlfiletags = etree.XPath(
        '//opf:item[@media-type="application/xhtml+xml"]', namespaces=OPFNS
    )(opftree)
    _linkfound = _unbfound = _ufound = _wmfound = metcharfound = False
    for _htmlfiletag in _htmlfiletags:
        _htmlfilepath = _htmlfiletag.get('href')
        parser = etree.XMLParser(recover=True)
        try:
            _xhtmlsoup = etree.fromstring(
                _epubfile.read(_folder + _htmlfilepath), parser
            )
        except:
            # First try replace %20 with spaces and check loading tree again
            complete_path = _folder + _htmlfilepath
            complete_path = complete_path.replace('%20', ' ')
            try:
                print('Potential problem with file path: ' +
                      _folder + _htmlfilepath)
                print('Replacing %20 with space and '
                      'trying load a file again...')
                _xhtmlsoup = etree.fromstring(
                    _epubfile.read(complete_path), parser
                )
                print('Loading succeed…')
            except:
                print('There is something wrong with file path: ' +
                      complete_path + ' Skipping...')
                continue
        if _wmfound is False:
            _watermarks = etree.XPath('//*[starts-with(text(),"==")]',
                                      namespaces=XHTMLNS)(_xhtmlsoup)
            if len(_watermarks) > 0:
                print(_file_dec + ': Potential problematic WM found')
                _wmfound = True

        if metcharfound is False:
            _metacharsets = etree.XPath('//xhtml:meta[@charset="utf-8"]',
                                        namespaces=XHTMLNS)(_xhtmlsoup)
            if len(_metacharsets) > 0:
                print(_file_dec + ': Problematic <meta '
                      'charset="utf-8" /> found.')
                metcharfound = True

        _alltexts = etree.XPath('//xhtml:body//text()',
                                namespaces=XHTMLNS)(_xhtmlsoup)
        _alltext = ' '.join(_alltexts)

        if _reftoccount == 0 and _alltext.find(u'Spis treści') != -1:
                print(_file_dec + ': Html TOC candidate found: ' +
                      _htmlfilepath)
        check_hyphs = False
        if check_hyphs:
            if not _ufound and _alltext.find(u'\u00AD') != -1:
                print(_file_dec + ': U+00AD hyphenate marks found.')
                _ufound = True
            if not _unbfound and _alltext.find(u'\u00A0') != -1:
                print(_file_dec + ': U+00A0 non-breaking space found.')
                _unbfound = True
        _links = etree.XPath('//xhtml:link', namespaces=XHTMLNS)(_xhtmlsoup)
        for _link in _links:
            if not _linkfound and (_link.get('type') is None):
                _linkfound = True
                print(_file_dec + ': At least one xhtml file has link tag '
                      'without type attribute defined')

    #Check dtb:uid - should be identical go dc:identifier
    ncxfile = etree.XPath('//opf:item[@media-type="application/x-dtbncx+xml"]',
                          namespaces=OPFNS)(opftree)[0].get('href')
    ncxtree = etree.fromstring(_epubfile.read(_folder + ncxfile))
    uniqid = etree.XPath('//opf:package',
                         namespaces=OPFNS)(opftree)[0].get('unique-identifier')
    if uniqid is not None:
        try:
            dc_identifier = etree.XPath('//dc:identifier[@id="' + uniqid +
                                        '"]/text()',
                                        namespaces=DCNS)(opftree)[0]
        except:
            dc_identifier = ''
            print(_file_dec + ': dc:identifier with unique-id not found')
    else:
        dc_identifier = ''
        print(_file_dec + ': no unique-identifier found')
    try:
        metadtd = etree.XPath('//ncx:meta[@name="dtb:uid"]',
                              namespaces=NCXNS)(ncxtree)[0]
        if metadtd.get('content') != dc_identifier:
            print(_file_dec + ': dtd:uid and dc:identifier mismatched')
    except IndexError:
        print(_file_dec + ': dtd:uid not properly defined')

    for meta in opftree.xpath("//opf:meta[starts-with(@name, 'calibre')]",
                              namespaces=OPFNS):
        print(_file_dec + ': calibre staff found')
        break
    for dcid in opftree.xpath(
        "//dc:identifier[@opf:scheme='calibre']",
        namespaces={'dc': 'http://purl.org/dc/elements/1.1/',
                    'opf': 'http://www.idpf.org/2007/opf'}
    ):
        print(_file_dec + ': other calibre staff found')
        break


def qcheck(_documents, _moded, _validator):
    if _moded:
        fe = '_moh.epub'
        nfe = '_org.epub'
    else:
        fe = '.epub'
        nfe = '_moh.epub'

    for root, dirs, files in os.walk(_documents):
        for _file in files:
            file_dec = _file.decode(sys.getfilesystemencoding())
            if _file.endswith(fe) and not _file.endswith(nfe):
                epubfile = zipfile.ZipFile(os.path.join(root, _file))
                for singlefile in epubfile.namelist():
                    if singlefile.find('.opf') > 0:
                        qcheck_single_file(singlefile, epubfile, file_dec)

                if _validator:
                    _epubchecker_path = os.path.join(
                        os.path.dirname(__file__), os.pardir, 'resources',
                        'epubcheck-3.0.1', 'epubcheck-3.0.1.jar'
                    )
                    print('*** EpubCheck 3.0.1 *** begin of validating '
                          'file: ' + file_dec)
                    subprocess.call(['java', '-jar', '%s' % _epubchecker_path,
                                    '%s' % str(os.path.join(root, _file))])
                    print('*** EpubCheck 3.0.1 *** end of validating '
                          'file: ' + file_dec)
                    print('')


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("directory",
                        help="Directory with EPUB files stored")
    parser.add_argument("-m", "--mod",
                        help="Check only _mod.epub files",
                        action="store_true")
    parser.add_argument("-p", "--epubcheck",
                        help="Validate files with epubcheck",
                        action="store_true")
    args = parser.parse_args()

    qcheck(args.directory, args.mod, args.epubcheck)
