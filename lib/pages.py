#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of ExtractCoverThumbs, licensed under
# GNU Affero GPLv3 or later.
# Copyright © Robert Błaut. See NOTICE for more information.
#


from __future__ import print_function
import os
import sys
import struct
import unicodedata

SFENC = sys.getfilesystemencoding()


class PalmDB:
    unique_id_seed = 68
    number_of_pdb_records = 76
    first_pdb_record = 78

    def __init__(self, palmdata):
        self.data = palmdata
        self.nsec, = struct.unpack_from('>H', self.data,
                                        PalmDB.number_of_pdb_records)

    def getsecaddr(self, secno):
        secstart, = struct.unpack_from('>L', self.data,
                                       PalmDB.first_pdb_record + secno * 8)
        if secno == self.nsec - 1:
            secend = len(self.data)
        else:
            secend, = struct.unpack_from(
                '>L', self.data,
                PalmDB.first_pdb_record + (secno + 1) * 8
            )
        return secstart, secend

    def readsection(self, secno):
        if secno < self.nsec:
            secstart, secend = self.getsecaddr(secno)
            return self.data[secstart:secend]
        return ''

    def getnumsections(self):
        return self.nsec


def find_exth(search_id, content):
    exth_begin = content.find('EXTH')
    exth_header = content[exth_begin:]
    count_items, = struct.unpack('>L', exth_header[8:12])
    pos = 12
    for _ in range(count_items):
        id, size = struct.unpack('>LL', exth_header[pos:pos + 8])
        exth_record = exth_header[pos + 8: pos + size]
        if id == search_id:
            return exth_record
        pos += size
    return '* NONE *'


def strip_accents(text):
    return ''.join(c for c in unicodedata.normalize(
        'NFKD', text
    ) if unicodedata.category(c) != 'Mn')


def mobi_header_fields(mobi_content):
    pp = PalmDB(mobi_content)
    header = pp.readsection(0)
    id = struct.unpack_from('4s', header, 0x10)[0]
    version = struct.unpack_from('>L', header, 0x24)[0]
    # dictionary input and output languages
    dict_input = struct.unpack_from('>L', header, 0x60)[0]
    dict_output = struct.unpack_from('>L', header, 0x64)[0]
    # number of locations
    text_length = struct.unpack('>I', header[4:8])[0]
    locations = text_length / 150 + 1
    # title
    toff, tlen = struct.unpack('>II', header[0x54:0x5c])
    tend = toff + tlen
    title = header[toff:tend]

    return id, version, title, locations, dict_input, dict_output


def get_pages(dirpath, mfile):
    file_dec = mfile.decode(sys.getfilesystemencoding())
    with open(os.path.join(dirpath, mfile), 'rb') as f:
        mobi_content = f.read()
    if mobi_content[60:68] != 'BOOKMOBI':
        print(file_dec + ': invalid file format. Skipping...')
        return None
    id, ver, title, locations, di, do = mobi_header_fields(mobi_content)
    if (di != 0 or do != 0):
        print(file_dec + ': dictionary file. Skipping...')
        return None
    author = find_exth(100, mobi_content)
    asin = find_exth(113, mobi_content)
    dc_lang = find_exth(524, mobi_content)
    if '!DeviceUpgradeLetter!' in asin:
        print(file_dec + ': Upgrade Letter. Skipping...')
        return None
    row = [
        asin,
        dc_lang,
        author,
        title,
        locations / 15 + 1,
        False,
        os.path.join(mfile)
    ]
    return row
