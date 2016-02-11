# -*- coding: utf-8 -*-

__license__ = 'GPL v3'
__copyright__ = '2011, John Schember <john at nachtimwald.com>'
__docformat__ = 'restructuredtext en'

'''
Generates and writes an APNX page mapping file.
'''

import struct
import os
import sys

import kindle_unpack
from lib.header import PdbHeaderReader


class APNXBuilder(object):
    """Create an APNX file using a pseudo page mapping."""

    def write_apnx(self, mobi_file_path, apnx_path, page_count=0):
        """
        Write APNX file.

        If you want a fixed number of pages (such as from a custom column) then
        pass in a value to page_count, otherwise a count will be estimated
        using either the fast or accurate algorithm.
        """
        import uuid
        apnx_meta = {'guid': str(uuid.uuid4()).replace('-', '')[:8], 'asin':
                     '', 'cdetype': 'EBOK', 'format': 'MOBI_7', 'acr': ''}

        try:
            with open(mobi_file_path, 'rb') as mf:
                ident = PdbHeaderReader(mf).identity()
                if ident != 'BOOKMOBI':
                    # Check that this is really a MOBI file.
                    print('ERROR! Not a valid MOBI file "%s"'
                          % os.path.basename(mobi_file_path))
                    return 1
                apnx_meta['acr'] = str(PdbHeaderReader(mf).name())
        except:
            print('Error! Unable to open file %s' % mobi_file_path)
            return 1
        # We'll need the PDB name, the MOBI version, and some metadata to make
        # FW 3.4 happy with KF8 files...
        with open(mobi_file_path, 'rb') as mf:
            section = kindle_unpack.Sectionizer(mobi_file_path)
            mhlst = [kindle_unpack.MobiHeader(section, 0)]
            mh = mhlst[0]
            metadata = mh.getmetadata()
            if mh.version == 8:
                apnx_meta['format'] = 'MOBI_8'
            else:
                apnx_meta['format'] = 'MOBI_7'
            try:
                if metadata['Document Type'][0] is None:
                    apnx_meta['cdetype'] = 'EBOK'
                else:
                    apnx_meta['cdetype'] = 'EBOK'
                    apnx_meta['cdetype'] = metadata['Document Type'][0]
            except KeyError:
                apnx_meta['cdetype'] = 'EBOK'
            try:
                if metadata['ASIN'][0] is None:
                    apnx_meta['asin'] = ''
                else:
                    apnx_meta['asin'] = metadata['ASIN'][0]
            except KeyError:
                apnx_meta['asin'] = ''

        # Get the pages depending on the chosen parser
        pages = []
        if page_count:
            pages = self.get_pages_exact(mobi_file_path, page_count)
        else:
            pages = self.get_pages_fast(mobi_file_path)

        if not pages:
            pages = self.get_pages_fast(mobi_file_path)
        if not pages:
            print('Could not generate page mapping.')
        if len(pages) > 65536:
            print('Pages over limit in "%s" file. '
                  'Unable to write apnx file...' % mobi_file_path)
            return

        # Generate the APNX file from the page mapping.
        apnx = self.generate_apnx(pages, apnx_meta)

        # Write the APNX.
        if sys.platform == 'win32':
            apnx_path = '\\\\?\\' + apnx_path.replace('/', '\\')
        with open(apnx_path, 'wb') as apnxf:
            apnxf.write(apnx)

    def generate_apnx(self, pages, apnx_meta):
        apnx = ''

        # Updated header if we have a KF8 file...
        if apnx_meta['format'] == 'MOBI_8':
            content_header = '{"contentGuid":"%(guid)s","asin":"%(asin)s","cdeType":"%(cdetype)s","format":"%(format)s","fileRevisionId":"1","acr":"%(acr)s"}' % apnx_meta  # noqa
        else:
            # My 5.1.x Touch & 3.4 K3 seem to handle the 'extended' header
            # fine for legacy mobi files, too. But, since they still handle
            # this one too, let's try not to break old devices, and keep using
            # the simple header ;).
            content_header = '{"contentGuid":"%(guid)s","asin":"%(asin)s","cdeType":"%(cdetype)s","fileRevisionId":"1"}' % apnx_meta  # noqa
        page_header = '{"asin":"%(asin)s","pageMap":"(1,a,1)"}' % apnx_meta

        apnx += struct.pack('>I', 65537)
        apnx += struct.pack('>I', 12 + len(content_header))
        apnx += struct.pack('>I', len(content_header))
        apnx += content_header
        apnx += struct.pack('>H', 1)
        apnx += struct.pack('>H', len(page_header))
        apnx += struct.pack('>H', len(pages))
        apnx += struct.pack('>H', 32)
        apnx += page_header

        # Write page values to APNX.
        for page in pages:
            apnx += struct.pack('>I', page)

        return apnx

    def get_pages_exact(self, mobi_file_path, page_count):
        """
        Get pages exact.

        Given a specified page count (such as from a custom column),
        create our array of pages for the apnx file by dividing by
        the content size of the book.
        """
        pages = []
        count = 0

        with open(mobi_file_path, 'rb') as mf:
            phead = PdbHeaderReader(mf)
            r0 = phead.section_data(0)
            text_length = struct.unpack('>I', r0[4:8])[0]

        chars_per_page = int(text_length / page_count)
        while count < text_length:
            pages.append(count)
            count += chars_per_page

        if len(pages) > page_count:
            # Rounding created extra page entries
            pages = pages[:page_count]

        return pages

    def get_pages_fast(self, mobi_file_path):
        """
        2300 characters of uncompressed text per page.

        This is not meant to map 1 to 1 to a print book but to be a
        close enough measure.

        A test book was chosen and the characters were counted
        on one page. This number was round to 2240 then 60
        characters of markup were added to the total giving
        2300.

        Uncompressed text length is used because it's easily
        accessible in MOBI files (part of the header). Also,
        It's faster to work off of the length then to
        decompress and parse the actual text.
        """
        text_length = 0
        pages = []
        count = 0

        with open(mobi_file_path, 'rb') as mf:
            phead = PdbHeaderReader(mf)
            r0 = phead.section_data(0)
            text_length = struct.unpack('>I', r0[4:8])[0]

        while count < text_length:
            pages.append(count)
            count += 2300

        return pages
