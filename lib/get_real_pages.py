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

    def get_pages(url):
        tree = get_html_page(url)
        pages = tree.xpath(
            '//div[@class="profil-desc-inline"]'
            '//dt[contains(text(),"liczba stron")]'
            '/following-sibling::dd/text()'
        )
        if pages:
            return pages[0]
        else:
            return None

    def get_search_results(tree):
        results = tree.xpath('*//div[contains(@class,"book-data")]')
        if len(results) == 1:
            book_url = results[0].xpath(
                './div[contains(@class,"book-general-data")]'
                '/a[@class="bookTitle"]/@href'
            )[0]
            return book_url
        else:
            print('* multiple results * ')
            return None
            # for result in results:
            #     title = result.xpath(
            #         './div[contains(@class,"book-general-data")]'
            #         '//a[@class="bookTitle"]//text()'
            #     )
            #     book_url = result.xpath(
            #         './div[contains(@class,"book-general-data")]'
            #         '/a[@class="bookTitle"]/@href'
            #     )
            #     authors = result.xpath(
            #         './div[contains(@class,"book-general-data")]'
            #         '//a[contains(@href,"autor")]//text()'
            #     )

    print(os.path.join(HOME, csvfile))
    if os.path.isfile(os.path.join(HOME, csvfile)):
        with open(os.path.join(HOME, csvfile)) as f:
            csvread = csv.reader(
                f, delimiter=';', quotechar='"',
                quoting=csv.QUOTE_ALL
            )
            for row in csvread:
                root = search_book(row[3])
                book_url = get_search_results(root)
                print(book_url)
                if book_url:
                    pages = get_pages(book_url)
                    print(pages)
get_real_pages('book-pages.csv')
