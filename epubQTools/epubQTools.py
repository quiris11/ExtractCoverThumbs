#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of pyBookTools, licensed under GNU Affero GPLv3 or later.
# Copyright © Robert Błaut. See NOTICE for more information.
#

import argparse
import os
import re
import tempfile
import shutil
import subprocess
import sys
import zipfile
from lxml import etree

sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
from hyphenator import Hyphenator
from epubqcheck import qcheck

_my_language = 'pl'
_hyphen_mark = u'\u00AD'
_hyph = Hyphenator(os.path.join(os.path.dirname(__file__), 'resources',
                   'dictionaries', 'hyph_pl_PL.dic'))

DTD = ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" '
       '"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">')
OPFNS = {'opf': 'http://www.idpf.org/2007/opf'}
XHTMLNS = {'xhtml': 'http://www.w3.org/1999/xhtml'}
DCNS = {'dc': 'http://purl.org/dc/elements/1.1/'}
NCXNS = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}
SVGNS = {'svg': 'http://www.w3.org/2000/svg'}

parser = argparse.ArgumentParser()
parser.add_argument("directory", help="Directory with EPUB files stored")
parser.add_argument("-q", "--qcheck", help="validate files with epubqcheck "
                    "internal tool",
                    action="store_true")
parser.add_argument("-p", "--epubcheck", help="validate epub files with "
                    " EpubCheck 3.0.1 tool",
                    action="store_true")
parser.add_argument("-m", "--mod", help="validate only _moh.epub files "
                    "(only with -q or -v)",
                    action="store_true")
parser.add_argument("-e", "--epub", help="fix and hyphenate original epub "
                    "files to _moh.epub files", action="store_true")
parser.add_argument("-r", "--resetmargins", help="reset CSS margins for "
                    "body, html and @page in _moh.epub files (only with -e)",
                    action="store_true")
parser.add_argument("-k", "--kindlegen", help="convert _moh.epub files to"
                    " .mobi with kindlegen", action="store_true")
parser.add_argument("-d", "--huffdic", help="tell kindlegen to use huffdic "
                    "compression (slow conversion)", action="store_true")
parser.add_argument("-v", "--verbose", help="more detailed output",
                    action="store_true")
parser.add_argument("-f", "--force",
                    help="overwrite previously generated _moh.epub or "
                    " .mobi files (only with -k or -e)",
                    action="store_true")
args = parser.parse_args()

_documents = args.directory
validator = args.epubcheck
verbose = args.verbose


def unpack_epub(source_epub):
    epubzipfile = zipfile.ZipFile(source_epub)
    tempdir = tempfile.mkdtemp()
    epubzipfile.extractall(tempdir)
    os.remove(os.path.join(tempdir, 'mimetype'))
    return epubzipfile, tempdir


def pack_epub(output_filename, source_dir):
    with zipfile.ZipFile(output_filename, "w") as zip:
        zip.writestr("mimetype", "application/epub+zip")
    relroot = source_dir
    with zipfile.ZipFile(output_filename, "a", zipfile.ZIP_DEFLATED) as zip:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                filename = os.path.join(root, file)
                if os.path.isfile(filename):
                    arcname = os.path.join(os.path.relpath(root, relroot),
                                           file)
                    zip.write(filename, arcname)


def clean_temp(sourcedir):
    if os.path.isdir(sourcedir):
        shutil.rmtree(sourcedir)


def find_xhtml_files(epubzipfile, tempdir):
    for singlefile in epubzipfile.namelist():
        if singlefile.find('.opf') > 0:
            if singlefile.find('/') == -1:
                rootepubdir = tempdir
            else:
                rootepubdir = os.path.join(tempdir,
                                           singlefile.split('/')[0])
            opftree = etree.fromstring(epubzipfile.read(singlefile))
            try:
                xhtml_items = etree.XPath(
                    '//opf:item[@media-type="application/xhtml+xml"]',
                    namespaces=OPFNS
                )(opftree)
            except:
                print('XHTML files not found...')
            xhtml_files = []
            xhtml_file_paths = []
            for xhtml_item in xhtml_items:
                xhtml_files.append(os.path.join(rootepubdir,
                                   xhtml_item.get('href')))
                xhtml_file_paths.append(xhtml_item.get('href'))
            opf_file = os.path.join(tempdir, singlefile)
            return xhtml_files, xhtml_file_paths, opf_file, rootepubdir


def hyphenate_and_fix_conjunctions(source_file, hyph, hyphen_mark):
    try:
        texts = etree.XPath(
            '//xhtml:body//text()',
            namespaces=XHTMLNS
        )(source_file)
    except:
        print('No texts found...')
    for t in texts:
        parent = t.getparent()
        newt = ''
        wlist = re.compile(r'\w+|[^\w]', re.UNICODE).findall(t)
        for w in wlist:
            newt += hyph.inserted(w, hyphen_mark)

        # fix for hanging single conjunctions
        newt = re.sub(r'(?<=\s\w)\s+', u'\u00A0', newt)
        if t.is_text:
            parent.text = newt
        elif t.is_tail:
            parent.tail = newt
    return source_file


def fix_styles(source_file):
    try:
        links = etree.XPath(
            '//xhtml:link',
            namespaces=XHTMLNS
        )(source_file)
    except:
        print('No links found...')
    for link in links:
        if link.get('type') is None:
            link.set('type', 'text/css')
    return source_file


def fix_html_toc(opf_file, tempdir, xhtml_files, xhtml_file_paths):
    soup = etree.parse(opf_file)
    reftocs = etree.XPath('//opf:reference[@type="toc"]',
                          namespaces=OPFNS)(soup)
    if len(reftocs) == 0:
        html_toc = None
        for xhtml_file in xhtml_files:
            xhtmltree = etree.parse(xhtml_file,
                                    parser=etree.XMLParser(recover=True))
            alltexts = etree.XPath('//text()', namespaces=XHTMLNS)(xhtmltree)
            alltext = ' '.join(alltexts)
            if alltext.find(u'Spis treści') != -1:
                html_toc = xhtml_file
                break
        if html_toc is not None:
            for xhtml_file_path in xhtml_file_paths:
                if xhtml_file_path.find(os.path.basename(html_toc)) != -1:
                    html_toc = xhtml_file_path
                    break
            newtocreference = etree.Element('reference', title='TOC',
                                            type="toc", href=html_toc)
            soup.xpath('//opf:guide',
                       namespaces=OPFNS)[0].insert(0, newtocreference)
        else:
            parser = etree.XMLParser(remove_blank_text=True)
            transform = etree.XSLT(etree.parse(os.path.join(
                os.path.dirname(__file__), 'resources', 'ncx2end-0.2.xsl'
            )))
            toc_ncx_file = etree.XPath(
                '//opf:item[@media-type="application/x-dtbncx+xml"]',
                namespaces=OPFNS
            )(soup)[0].get('href')
            ncxtree = etree.parse(os.path.join(tempdir, toc_ncx_file), parser)
            result = transform(ncxtree)
            with open(os.path.join(tempdir, 'toc-quiris.xhtml'), "w") as f:
                f.write(etree.tostring(
                    result,
                    pretty_print=True,
                    xml_declaration=True,
                    encoding="utf-8",
                    doctype=DTD
                ))
            newtocmanifest = etree.Element(
                '{http://www.idpf.org/2007/opf}item',
                attrib={'media-type': 'application/xhtml+xml',
                        'href': 'toc-quiris.xhtml', 'id': 'toc-quiris'}
            )
            soup.xpath('//opf:manifest',
                       namespaces=OPFNS)[0].insert(0, newtocmanifest)
            newtocspine = etree.Element(
                '{http://www.idpf.org/2007/opf}itemref',
                idref='toc-quiris'
            )
            soup.xpath('//opf:spine', namespaces=OPFNS)[0].append(newtocspine)
            newtocreference = etree.Element(
                '{http://www.idpf.org/2007/opf}reference',
                title='TOC',
                type="toc",
                href='toc-quiris.xhtml'
            )
            try:
                soup.xpath('//opf:guide',
                           namespaces=OPFNS)[0].insert(0, newtocreference)
            except IndexError:
                newguide = etree.Element('{http://www.idpf.org/2007/opf}guide')
                newguide.append(newtocreference)
                soup.xpath('//opf:package',
                           namespaces=OPFNS)[0].append(newguide)

    with open(opf_file, "w") as f:
        f.write(etree.tostring(
            soup.getroot(),
            pretty_print=True,
            xml_declaration=True,
            encoding='utf-8'
        ))


def fix_various_opf_problems(source_file, tempdir, xhtml_files,
                             xhtml_file_paths):
    soup = etree.parse(source_file)

    # remove multiple dc:language
    lang_counter = 0
    for lang in soup.xpath("//dc:language", namespaces=DCNS):
        lang_counter = lang_counter + 1
        if lang_counter > 1:
            lang.getparent().remove(lang)

    # set dc:language to my language
    for lang in soup.xpath("//dc:language", namespaces=DCNS):
        if lang.text != _my_language:
            lang.text = _my_language

    # add missing dc:language
    if len(soup.xpath("//dc:language", namespaces=DCNS)) == 0:
        for metadata in soup.xpath("//opf:metadata", namespaces=OPFNS):
            newlang = etree.Element(
                '{http://purl.org/dc/elements/1.1/}language'
            )
            newlang.text = _my_language
            metadata.insert(0, newlang)

    # add missing meta cover
    metacovers = etree.XPath('//opf:meta[@name="cover"]',
                             namespaces=OPFNS)(soup)
    refcovers = etree.XPath('//opf:reference[@type="cover"]',
                            namespaces=OPFNS)(soup)
    if len(metacovers) == 1:
        itemcovers = etree.XPath(
            '//opf:item[@id="' + metacovers[0].get('content') + '"]',
            namespaces=OPFNS
        )(soup)

        # find html cover file
        if len(refcovers) == 0:
            if verbose:
                print('Defining cover guide element...')
            itemcoverhref = os.path.basename(itemcovers[0].get('href'))
            cover_file = None
            for xhtml_file in xhtml_files:
                xhtmltree = etree.parse(xhtml_file,
                                        parser=etree.XMLParser(recover=True))

                allimgs = etree.XPath('//xhtml:img',
                                      namespaces=XHTMLNS)(xhtmltree)
                for img in allimgs:
                    if img.get('src').find(itemcoverhref) != -1:
                        cover_file = xhtml_file
                        break

                allsvgimgs = etree.XPath('//svg:image',
                                         namespaces=SVGNS)(xhtmltree)
                for svgimg in allsvgimgs:
                    if svgimg.get('{http://www.w3.org/1999/xlink}href').find(
                        itemcoverhref
                    ) != -1:
                        cover_file = xhtml_file
                        break
            if cover_file is not None:
                for xhtml_file_path in xhtml_file_paths:
                    if xhtml_file_path.find(
                            os.path.basename(cover_file)
                    ) != -1:
                        cover_file = xhtml_file_path
                        break
                newcoverreference = etree.Element(
                    'reference', title='Cover',
                    type="cover",   href=cover_file
                )
                soup.xpath('//opf:guide',
                           namespaces=OPFNS)[0].insert(0, newcoverreference)
                if verbose:
                    print('Cover guide element defined...')
            else:
                print('Unable to find html cover file. Probably '
                      'different cover images for meta cover and '
                      'html cover...')
    else:
        itemcovers = []
    if len(metacovers) == 0 or len(itemcovers) == 0:
        refcovers = etree.XPath('//opf:reference[@type="cover"]',
                                namespaces=OPFNS)(soup)
        cover_image = None
        if len(refcovers) == 1:
            coversoup = etree.parse(
                os.path.join(tempdir, refcovers[0].get('href')),
                parser=etree.XMLParser(recover=True)
            )
            if etree.tostring(coversoup) is not None:
                imgs = etree.XPath('//xhtml:img',
                                   namespaces=XHTMLNS)(coversoup)
                if len(imgs) == 1:
                    cover_image = imgs[0].get('src')
                images = etree.XPath('//svg:image',
                                     namespaces=SVGNS)(coversoup)
                if len(imgs) == 0 and len(images) == 1:
                    cover_image = images[0].get(
                        '{http://www.w3.org/1999/xlink}href'
                    )
        if cover_image is not None:
            cover_image = re.sub('^\.\.\/', '', cover_image)
            itemhrefcovers = etree.XPath(
                '//opf:item[translate(@href, "ABCDEFGHJIKLMNOPQRSTUVWXYZ", '
                '"abcdefghjiklmnopqrstuvwxyz")="' + cover_image.lower() +
                '"]', namespaces=OPFNS
            )(soup)
            if len(itemhrefcovers) == 1:
                metadatas = etree.XPath('//opf:metadata',
                                        namespaces=OPFNS)(soup)

                if len(metadatas) == 1 and len(metacovers) == 0:
                    newmeta = etree.Element(
                        'meta', name='cover',
                        content=itemhrefcovers[0].get('id')
                    )
                    metadatas[0].insert(0, newmeta)
                elif len(metadatas) == 1 and len(metacovers) == 1:
                    metacovers[0].set('content', itemhrefcovers[0].get('id'))

    # remove calibre staff
    for meta in soup.xpath("//opf:meta[starts-with(@name, 'calibre')]",
                           namespaces=OPFNS):
        meta.getparent().remove(meta)
    for dcid in soup.xpath(
            "//dc:identifier[@opf:scheme='calibre']",
            namespaces={'dc': 'http://purl.org/dc/elements/1.1/',
                        'opf': 'http://www.idpf.org/2007/opf'}
            ):
        dcid.getparent().remove(dcid)

    with open(source_file, "w") as f:
        f.write(etree.tostring(soup.getroot(), pretty_print=True,
                xml_declaration=True, encoding='utf-8'))


def fix_ncx_dtd_uid(source_file, tempdir):
    opftree = etree.parse(source_file)
    ncxfile = etree.XPath(
        '//opf:item[@media-type="application/x-dtbncx+xml"]',
        namespaces=OPFNS
    )(opftree)[0].get('href')
    ncxtree = etree.parse(os.path.join(tempdir, ncxfile))
    uniqid = etree.XPath('//opf:package',
                         namespaces=OPFNS)(opftree)[0].get('unique-identifier')
    if uniqid is None:
        dcidentifiers = etree.XPath('//dc:identifier',
                                    namespaces=DCNS)(opftree)
        for dcid in dcidentifiers:
            if dcid.get('id') is not None:
                uniqid = dcid.get('id')
                break
        opftree.xpath('//opf:package',
                      namespaces=OPFNS)[0].set('unique-identifier', uniqid)
        with open(source_file, "w") as f:
            f.write(etree.tostring(opftree.getroot(), pretty_print=True,
                                   xml_declaration=True, encoding='utf-8'))
    dc_identifier = etree.XPath('//dc:identifier[@id="' + uniqid + '"]/text()',
                                namespaces=DCNS)(opftree)[0]
    try:
        metadtd = etree.XPath('//ncx:meta[@name="dtb:uid"]',
                              namespaces=NCXNS)(ncxtree)[0]
    except IndexError:
        newmetadtd = etree.Element(
            '{http://www.daisy.org/z3986/2005/ncx/}meta',
            attrib={'name': 'dtb:uid', 'content': ''}
        )
        ncxtree.xpath('//ncx:head', namespaces=NCXNS)[0].append(newmetadtd)
        metadtd = etree.XPath('//ncx:meta[@name="dtb:uid"]',
                              namespaces=NCXNS)(ncxtree)[0]
    if metadtd.get('content') != dc_identifier:
        metadtd.set('content', dc_identifier)
    with open(os.path.join(tempdir, ncxfile), 'w') as f:
        f.write(etree.tostring(ncxtree.getroot(), pretty_print=True,
                xml_declaration=True, encoding='utf-8'))


def append_reset_css(source_file):
    if verbose:
        print('Resetting CSS body margin and padding...')
    try:
        heads = etree.XPath(
            '//xhtml:head',
            namespaces=XHTMLNS
        )(source_file)
    except:
        print('No head found...')
    heads[0].append(etree.fromstring(
        '<style type="text/css">'
        '@page { margin: 5pt } '
        'body { margin: 5pt; padding: 0 }'
        '</style>'
    ))
    return source_file


def main():
    if args.qcheck:
        qcheck(_documents, args.mod, args.epubcheck)
    elif args.kindlegen:
        compression = '-c2' if args.huffdic else '-c1'
        for root, dirs, files in os.walk(_documents):
            if verbose:
                kwargs = {}
            else:
                devnull = open(os.devnull, 'w')
                kwargs = {'stdout': devnull, 'stderr': devnull}
            for _file in files:
                if _file.endswith('_moh.epub'):
                    newmobifile = os.path.splitext(_file)[0] + '.mobi'
                    if not args.force:
                        if os.path.isfile(os.path.join(root, newmobifile)):
                            print(
                                'Skipping previously generated _moh file: ' +
                                newmobifile
                            )
                            continue
                    print('')
                    print('Kindlegen: Converting file: ' +
                          _file.decode(sys.getfilesystemencoding()))
                    retcode = subprocess.call(['kindlegen', compression,
                                              os.path.join(root, _file)],
                                              **kwargs)
                    if retcode == 1:
                        print('MOBI file built with WARNINGS!')
                    elif retcode == 2:
                        print('ERROR! Building MOBI file process aborted!')
                    elif retcode == 0:
                        print('MOBI file built successfully.')

    elif args.epub:
        for root, dirs, files in os.walk(_documents):
            for _file in files:
                if (_file.endswith('.epub') and
                        not _file.endswith('_moh.epub') and
                        not _file.endswith('_org.epub')):
                    _newfile = os.path.splitext(_file)[0] + '_moh.epub'

                    # if not forced skip previously generated files
                    if not args.force:
                        if os.path.isfile(os.path.join(root, _newfile)):
                            print(
                                'Skipping previously generated _moh file: ' +
                                _newfile
                            )
                            continue

                    print('')
                    print('Working on: ' +
                          _file.decode(sys.getfilesystemencoding()))
                    _epubzipfile, _tempdir = unpack_epub(
                        os.path.join(root, _file)
                    )

                    # remove obsolete calibre_bookmarks.txt
                    try:
                        os.remove(os.path.join(
                            _tempdir, 'META-INF', 'calibre_bookmarks.txt'
                        ))
                    except OSError:
                        pass

                    (
                        _xhtml_files,
                        _xhtml_file_paths,
                        _opf_file,
                        _rootepubdir
                    ) = find_xhtml_files(_epubzipfile, _tempdir)
                    fix_various_opf_problems(
                        _opf_file, _rootepubdir,
                        _xhtml_files, _xhtml_file_paths
                    )
                    fix_ncx_dtd_uid(_opf_file, _rootepubdir)
                    fix_html_toc(
                        _opf_file, _rootepubdir,
                        _xhtml_files, _xhtml_file_paths
                    )
                    for _single_xhtml in _xhtml_files:
                        with open(_single_xhtml, 'r') as content_file:
                            c = content_file.read()
                            c = c.replace('&shy;', '')
                            c = c.replace('&nbsp;', ' ')
                        _xhtmltree = etree.fromstring(
                            c, parser=etree.XMLParser(recover=False)
                        )
                        _xhtmltree = hyphenate_and_fix_conjunctions(
                            _xhtmltree, _hyph, _hyphen_mark
                        )
                        _xhtmltree = fix_styles(_xhtmltree)

                        if args.resetmargins:
                            _xhtmltree = append_reset_css(_xhtmltree)

                        # remove watermarks
                        _wmarks = etree.XPath(
                            '//xhtml:span[starts-with(text(), "==")]',
                            namespaces=XHTMLNS
                        )(_xhtmltree)
                        for wm in _wmarks:
                            wm.getparent().remove(wm)

                        # remove meta charsets
                        _metacharsets = etree.XPath(
                            '//xhtml:meta[@charset="utf-8"]',
                            namespaces=XHTMLNS
                        )(_xhtmltree)
                        for mch in _metacharsets:
                            mch.getparent().remove(mch)

                        with open(_single_xhtml, "w") as f:
                            f.write(etree.tostring(
                                _xhtmltree,
                                pretty_print=True,
                                xml_declaration=True,
                                encoding="utf-8",
                                doctype=DTD)
                            )
                    pack_epub(os.path.join(root, _newfile),
                              _tempdir)
                    clean_temp(_tempdir)
                    print('Done...')
    else:
        parser.print_help()
        print("* * *")
        print("* At least one of above optional arguments is required.")
        print("* * *")
    return 0

if __name__ == '__main__':
    sys.exit(main())
