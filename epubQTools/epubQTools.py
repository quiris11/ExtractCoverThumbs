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
if not hasattr(sys, 'frozen'):
    sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
from hyphenator import Hyphenator
from epubqcheck import qcheck

_my_language = 'pl'
_hyphen_mark = u'\u00AD'
if not hasattr(sys, 'frozen'):
    _hyph = Hyphenator(os.path.join(os.path.dirname(__file__), 'resources',
                       'dictionaries', 'hyph_pl_PL.dic'))
else:
    _hyph = Hyphenator(os.path.join(os.path.dirname(sys.executable),
                       'resources', 'dictionaries', 'hyph_pl_PL.dic'))

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
parser.add_argument("-c", "--findcover", help="force find cover (risky) "
                    "(only with -e)",
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
            newtocreference = etree.Element(
                '{http://www.idpf.org/2007/opf}reference', title='TOC',
                type='toc', href=html_toc
            )
        else:
            parser = etree.XMLParser(remove_blank_text=True)
            if not hasattr(sys, 'frozen'):
                transform = etree.XSLT(etree.parse(os.path.join(
                    os.path.dirname(__file__), 'resources', 'ncx2end-0.2.xsl'
                )))
            else:
                transform = etree.XSLT(etree.parse(os.path.join(
                    os.path.dirname(sys.executable), 'resources',
                    'ncx2end-0.2.xsl'
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
                type='toc',
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

    with open(opf_file, 'w') as f:
        f.write(etree.tostring(
            soup.getroot(),
            pretty_print=True,
            xml_declaration=True,
            encoding='utf-8'
        ))


def set_cover_guide_ref(_xhtml_files, _itemcoverhref, _xhtml_file_paths,
                        _soup):
    cover_file = None
    for xhtml_file in _xhtml_files:
        xhtmltree = etree.parse(xhtml_file,
                                parser=etree.XMLParser(recover=True))

        allimgs = etree.XPath('//xhtml:img', namespaces=XHTMLNS)(xhtmltree)
        for img in allimgs:
            if (img.get('src').find(_itemcoverhref) != -1 or
                    img.get('src').find('okladka_fmt') != -1):
                cover_file = xhtml_file
                break
        allsvgimgs = etree.XPath('//svg:image', namespaces=SVGNS)(xhtmltree)
        for svgimg in allsvgimgs:
            svg_img_href = svgimg.get('{http://www.w3.org/1999/xlink}href')
            if (svg_img_href.find(itemcoverhref) != -1 or
                    svg_img_href.find('okladka_fmt') != -1):
                cover_file = xhtml_file
                break
    if cover_file is not None:
        for xhtml_file_path in _xhtml_file_paths:
            if xhtml_file_path.find(os.path.basename(cover_file)) != -1:
                cover_file = xhtml_file_path
                break
        _newcoverreference = etree.Element(
            'reference', title='Cover',
            type="cover",   href=cover_file
        )
        _refcovers = etree.XPath('//opf:reference[@type="cover"]',
                                 namespaces=OPFNS)(_soup)
        try:
            if len(_refcovers) == 1:
                _refcovers[0].set('href', cover_file)
            else:
                _soup.xpath('//opf:guide',
                            namespaces=OPFNS)[0].insert(0, _newcoverreference)
        except IndexError:
            newguide = etree.Element('{http://www.idpf.org/2007/opf}guide')
            newguide.append(_newcoverreference)
            _soup.xpath('//opf:package',
                        namespaces=OPFNS)[0].append(newguide)
    return _soup


def set_cover_meta_elem(_metacovers, _soup, _content):
    _metadatas = etree.XPath('//opf:metadata', namespaces=OPFNS)(_soup)
    if len(_metadatas) == 1 and len(_metacovers) == 0:
        _newmeta = etree.Element('meta', name='cover', content=_content)
        _metadatas[0].insert(0, _newmeta)
    elif len(_metadatas) == 1 and len(_metacovers) == 1:
        _metacovers[0].set('content', _content)


def force_cover_find(_soup):
    if verbose:
        print('Force cover find...')
    images = etree.XPath('//opf:item[@media-type="image/jpeg"]',
                         namespaces=OPFNS)(_soup)
    cover_found = 0
    if len(images) != 0:
        for imag in images:
            img_href_lower = imag.get('href').lower()
            if (img_href_lower.find('cover') != -1 or
                    img_href_lower.find('okladka') != -1):
                cover_found = 1
                if verbose:
                    print('Candidate image for cover found:' +
                          ' href=' + imag.get('href') +
                          ' id=' + imag.get('id'))
                return imag.get('href'), imag.get('id')
                break
    if cover_found == 0:
        return None, None


def set_correct_font_mime_types(_soup):
    if verbose:
        print('Setting correct font mime types...')
    _items = etree.XPath('//opf:item[@href]', namespaces=OPFNS)(_soup)
    for _item in _items:
        if _item.get('href').endswith('.otf'):
            _item.set('media-type', 'application/vnd.ms-opentype')
        elif _item.get('href').endswith('.ttf'):
            _item.set('media-type', 'application/x-font-truetype')
    return _soup


def fix_various_opf_problems(source_file, tempdir, xhtml_files,
                             xhtml_file_paths):
    soup = etree.parse(source_file)

    soup = set_correct_font_mime_types(soup)

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

    # add missing meta cover and cover reference guide element
    metacovers = etree.XPath('//opf:meta[@name="cover"]',
                             namespaces=OPFNS)(soup)
    refcovers = etree.XPath('//opf:reference[@type="cover"]',
                            namespaces=OPFNS)(soup)
    if len(metacovers) == 1 and len(refcovers) == 0:
        # set missing cover reference guide element
        itemcovers = etree.XPath(
            '//opf:item[@id="' + metacovers[0].get('content') + '"]',
            namespaces=OPFNS
        )(soup)
        if verbose:
            print('Defining cover guide element...')
        itemcoverhref = os.path.basename(itemcovers[0].get('href'))
        soup = set_cover_guide_ref(
            xhtml_files, itemcoverhref, xhtml_file_paths, soup
        )

    elif len(metacovers) == 0 and len(refcovers) == 1:
        # set missing cover meta element
        cover_image = None
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
        else:
            imag_href, imag_id = force_cover_find(soup)
            if imag_href is not None and imag_id is not None:
                soup = set_cover_guide_ref(
                    xhtml_files, imag_href, xhtml_file_paths, soup
                )
                set_cover_meta_elem(metacovers, soup, imag_id)
            else:
                print('No images found...')
        if cover_image is not None:
            cover_image = re.sub('^\.\.\/', '', cover_image)
            itemhrefcovers = etree.XPath(
                '//opf:item[translate(@href, "ABCDEFGHJIKLMNOPQRSTUVWXYZ", '
                '"abcdefghjiklmnopqrstuvwxyz")="' + cover_image.lower() +
                '"]', namespaces=OPFNS
            )(soup)
            if len(itemhrefcovers) == 1:
                set_cover_meta_elem(
                    metacovers, soup, itemhrefcovers[0].get('id')
                )

    elif len(metacovers) == 0 and len(refcovers) == 0 and args.findcover:
        imag_href, imag_id = force_cover_find(soup)
        if imag_href is not None and imag_id is not None:
            soup = set_cover_guide_ref(
                xhtml_files, imag_href, xhtml_file_paths, soup
            )
            set_cover_meta_elem(metacovers, soup, imag_id)
        else:
            print('No images found...')

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

    # name='cover' should be before content attribute
    for cover in soup.xpath('//opf:meta[@name="cover" and @content]',
                            namespaces=OPFNS):
        cover.set('content', cover.attrib.pop('content'))

    with open(source_file, 'w') as f:
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
            for _file in files:
                if _file.endswith('_moh.epub'):
                    newmobifile = os.path.splitext(_file)[0] + '.mobi'
                    if not args.force:
                        if os.path.isfile(os.path.join(root, newmobifile)):
                            print(
                                'Skipping previously generated _moh file: ' +
                                newmobifile.decode(sys.getfilesystemencoding())
                            )
                            continue
                    print('')
                    print('Kindlegen: Converting file: ' +
                          _file.decode(sys.getfilesystemencoding()))
                    proc = subprocess.Popen([
                        'kindlegen', compression, os.path.join(root, _file)
                    ], stdout=subprocess.PIPE).communicate()[0]

                    cover_html_found = False
                    for ln in proc.splitlines():
                        if ln.find('Warning') != -1:
                            print ln
                        if ln.find('Error') != -1:
                            print ln
                        if ln.find('I1052') != -1:
                            cover_html_found = True
                    if not cover_html_found:
                        print('')
                        print(
                            'WARNING: Probably duplicated covers '
                            'generated in file: ' +
                            newmobifile.decode(sys.getfilesystemencoding())
                        )

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
                                _newfile.decode(sys.getfilesystemencoding())
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
                            c = c.replace('&ensp;', ' ')
                            c = c.replace('&ndash;', '–')
                            c = c.replace('&copy;', '©')
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
