#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of ExtractCoverThumbs, licensed under
# GNU Affero GPLv3 or later.
# Copyright © Robert Błaut. See NOTICE for more information.
#
# This script extracts missing Cover Thumbnails from eBooks downloaded
# from Amazon Personal Documents Service and side loads them
# to your Kindle Paperwhite.
#
from __future__ import print_function


def get_real_pages(csvfile):

    from lxml.html import fromstring
    import os
    import csv
    import urllib
    import urllib2
    HOME = os.path.expanduser("~")

    def get_html_page(url):
        req = urllib2.Request(url)
        return fromstring(urllib2.urlopen(req).read())

    def search_book(category):
        url = 'http://lubimyczytac.pl/szukaj/ksiazki'
        data = urllib.urlencode({
            'phrase': category,
            'main_search': '1',
        })
        url = url + '?' + data
        return get_html_page(url)

    def get_pages_book_type(url):
        tree = get_html_page(url)
        pages = tree.xpath(
            '//div[@class="profil-desc-inline"]'
            '//dt[contains(text(),"liczba stron")]'
            '/following-sibling::dd/text()'
        )
        book_types = tree.xpath('//div[contains(@class, "cover-book-type")]')
        if book_types:
            book_type = book_types[0].text
        else:
            book_type = ''
        if pages:
            return pages[0], book_type
        else:
            return None, book_type

    def get_search_results(tree, author, title):
        results = tree.xpath('*//div[contains(@class,"book-data")]')
        if len(results) == 1:
            book_url = results[0].xpath(
                './div[contains(@class,"book-general-data")]'
                '/a[@class="bookTitle"]/@href'
            )[0]
            return book_url
        else:
            for result in results:
                try:
                    title_f = result.xpath(
                        './div[contains(@class,"book-general-data")]'
                        '//a[@class="bookTitle"]//text()'
                    )[0]
                except IndexError:
                    title_f = ''
                try:
                    author_f = result.xpath(
                        './div[contains(@class,"book-general-data")]'
                        '//a[contains(@href,"autor")]//text()'
                    )[0]
                except IndexError:
                    author_f = ''
                book_url = result.xpath(
                    './div[contains(@class,"book-general-data")]'
                    '/a[@class="bookTitle"]/@href'
                )[0]
                if len(title) > len(title_f):
                    sub_title = len(title_f)
                else:
                    sub_title = len(title)
                if title[:sub_title].lower() == title_f[
                    :sub_title
                ].lower().encode('UTF-8'):
                    if author.lower() == author_f.lower().encode('UTF-8'):
                        return book_url
                        break

    if os.path.isfile(os.path.join(HOME, csvfile)):
        with open(os.path.join(HOME, csvfile), 'rb') as f:
            csvread = csv.reader(
                f, delimiter=';', quotechar='"',
                quoting=csv.QUOTE_ALL
            )
            dumped_list = list(csvread)
            for row in dumped_list:
                if row[0] == 'asin' or row[5] == 'True':
                    continue
                print('* Searching for: ' + row[2] + ' - ' + row[3])
                try:
                    root = search_book(row[3])
                except urllib2.HTTPError:
                    print('! HTTP error. Unable to find the book details...')
                    continue
                book_url = get_search_results(root, row[2], row[3])
                if book_url:
                    pages, book_type = get_pages_book_type(book_url)
                    if pages is not None:
                        row[4] = pages
                        row[5] = True
                        print('Liczba stron: ', pages)
                    elif book_type == 'E-book':
                        print('! E-book format only! '
                              'Using computed pages as real pages...')
                        row[5] = True
                    else:
                        print('! There are no pages found '
                              'on the site: ' + book_url)
                with open(os.path.join(HOME, csvfile), 'wb') as f:
                    csvwrite = csv.writer(
                        f, delimiter=';', quotechar='"',
                        quoting=csv.QUOTE_ALL
                    )
                    csvwrite.writerows(dumped_list)
get_real_pages('book-pages.csv')
