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

__license__ = 'GNU Affero GPL v3'
__copyright__ = '2014, Robert Błaut listy@blaut.biz'
__appname__ = u'ExtractCoverThumbs'
numeric_version = (0, 9)
__version__ = u'.'.join(map(unicode, numeric_version))
__author__ = u'Robert Błaut <listy@blaut.biz>'

import threading
from ExtractCoverThumbs import extract_cover_thumbs
import Tkinter as tk
from ScrolledText import ScrolledText
import tkFileDialog
import sys
import os


class App:

    def __init__(self, master):

        class IORedirector(object):
            def __init__(self, stext):
                self.stext = stext

        class StdoutRedirector(IORedirector):
            def write(self, str):
                self.stext.insert(tk.END, str)
                self.stext.see(tk.END)

        self.skip_apnx = tk.BooleanVar()
        self.is_azw = tk.BooleanVar()
        self.is_log = tk.BooleanVar()
        self.nac = tk.IntVar()
        self.is_fix_thumb = tk.BooleanVar()
        self.is_overwrite_pdoc_thumbs = tk.BooleanVar()
        self.is_overwrite_amzn_thumbs = tk.BooleanVar()
        self.is_overwrite_apnx = tk.BooleanVar()
        self.kindlepath = tk.StringVar()
        self.status = tk.StringVar()
        self.days = tk.StringVar()

        self.frame = tk.Frame(master, borderwidth=5)
        self.frame.pack(side=tk.TOP, anchor=tk.W)

        self.chk_button = tk.Button(self.frame, text="Choose Kindle",
                                    command=self.askdirectory, width=15)
        self.chk_button.pack(side=tk.LEFT)

        self.kindle_label = tk.Label(self.frame, textvariable=self.kindlepath)
        self.kindle_label.pack(side=tk.LEFT)

        self.frame2 = tk.Frame(master, borderwidth=5)
        self.frame2.pack(side=tk.TOP, pady=5)

        self.frame3 = tk.Frame(
            self.frame2,
        )
        self.frame3.pack(side=tk.TOP, anchor=tk.W)

        self.days_entry = tk.Entry(
            self.frame3, width=4,
            textvariable=self.days,
            state=tk.DISABLED
        )
        self.days_entry.pack(side=tk.RIGHT, anchor=tk.NW)

        self.days_checkbox = tk.Checkbutton(
            self.frame3,
            text="Process only younger files than days provided: ",
            variable=self.nac,
            command=self.naccheck
        )
        self.days_checkbox.deselect()
        self.days_checkbox.pack(side=tk.TOP, anchor=tk.NW)

        self.log_checkbox = tk.Checkbutton(
            self.frame2, text="Write less informations in Message Window?",
            variable=self.is_log
        )
        self.log_checkbox.deselect()
        self.log_checkbox.pack(side=tk.TOP, anchor=tk.NW)

        self.apnx_checkbox = tk.Checkbutton(
            self.frame2, text="Skip generating book page numbers "
                              "(APNX files)?",
            variable=self.skip_apnx
        )
        self.apnx_checkbox.deselect()
        self.apnx_checkbox.pack(side=tk.TOP, anchor=tk.NW)

        self.fix_thumb_checkbox = tk.Checkbutton(
            self.frame2, text="Fix book covers for PERSONAL badge? "
                              "(recommended for firmwares < 5.7.2)",
            variable=self.is_fix_thumb
        )
        self.fix_thumb_checkbox.deselect()
        self.fix_thumb_checkbox.pack(side=tk.TOP, anchor=tk.NW)

        self.labelframe = tk.LabelFrame(
            self.frame2,
            text=" For special needs. Use with caution! ",
            padx=5, pady=5
        )
        self.labelframe.pack(fill="both", expand="yes", pady=10)

        self.over_pdoc_thumbs_checkbox = tk.Checkbutton(
            self.labelframe,
            text="Overwrite existing personal documents (PDOC) covers?",
            variable=self.is_overwrite_pdoc_thumbs
        )

        self.over_pdoc_thumbs_checkbox.deselect()
        self.over_pdoc_thumbs_checkbox.pack(side=tk.TOP, anchor=tk.NW)

        self.over_amzn_thumbs_checkbox = tk.Checkbutton(
            self.labelframe,
            text="Overwrite existing amzn book (EBOK) and book sample (EBSP) "
                 "covers?",
            variable=self.is_overwrite_amzn_thumbs
        )

        self.over_amzn_thumbs_checkbox.deselect()
        self.over_amzn_thumbs_checkbox.pack(side=tk.TOP, anchor=tk.NW)

        self.over_apnx_checkbox = tk.Checkbutton(
            self.labelframe,
            text="Overwrite existing book page numbers (APNX files)?",
            variable=self.is_overwrite_apnx
        )

        self.over_apnx_checkbox.deselect()
        self.over_apnx_checkbox.pack(side=tk.TOP, anchor=tk.NW)

        self.azw_checkbox = tk.Checkbutton(
            self.labelframe,
            text="Extract covers from AZW files?",
            variable=self.is_azw
        )
        self.azw_checkbox.deselect()
        self.azw_checkbox.pack(side=tk.TOP, anchor=tk.NW)

        self.frame3 = tk.Frame(master, borderwidth=5)
        self.frame3.pack(side=tk.TOP, anchor=tk.W)

        self.run_button = tk.Button(self.frame3, text="Start",
                                    command=self.runthread,
                                    width=15)
        self.run_button.pack(side=tk.LEFT)

        self.status_label = tk.Label(self.frame3, textvariable=self.status)
        self.status_label.pack(side=tk.LEFT, pady=5)

        self.frame4 = tk.Frame(master, borderwidth=5)
        self.frame4.pack(side=tk.TOP)

        self.msg1 = 'Message Window: \n'
        self.stext = ScrolledText(self.frame4, bd=1, wrap=tk.WORD,
                                  height=25, width=100, relief=tk.RIDGE)
        if sys.platform == 'win32':
            self.stext.config(font=('Courier', 9, 'normal'))
        self.stext.pack()
        self.stext.insert(tk.END, self.msg1)

        sys.stdout = StdoutRedirector(self.stext)

    def naccheck(self):
        if self.nac.get() == 0:
            self.days_entry.delete(0, tk.END)
            self.days_entry.configure(state='disabled')
        else:
            self.days_entry.configure(state='normal')

    def runthread(self):
        thread1 = threading.Thread(target=self.run)
        thread1.start()

    def run(self):
        self.docs = os.path.join(self.kindlepath.get(), 'documents')
        self.stext.delete(1.0, tk.END)
        self.status.set('Processing your books... Please WAIT PATIENTLY!')
        self.frame.update_idletasks()
        if self.days.get() == '':
            extract_cover_thumbs(
                self.is_log.get(), self.is_overwrite_pdoc_thumbs.get(),
                self.is_overwrite_amzn_thumbs.get(),
                self.is_overwrite_apnx.get(),
                self.skip_apnx.get(), self.kindlepath.get(),
                self.docs, self.is_azw, None,
                self.is_fix_thumb.get()
            )
        else:
            extract_cover_thumbs(
                self.is_log.get(), self.is_overwrite_pdoc_thumbs.get(),
                self.is_overwrite_amzn_thumbs.get(),
                self.is_overwrite_apnx.get(),
                self.skip_apnx.get(), self.kindlepath.get(),
                self.docs, self.is_azw, self.days.get(),
                self.is_fix_thumb.get()

            )
        self.status.set('Process FINISHED! '
                        'You can SAFELY unmount Kindle device…')

    def askdirectory(self):
        if sys.platform == 'win32':
            a = tkFileDialog.askdirectory(initialdir="c:/")
        else:
            a = tkFileDialog.askdirectory(initialdir="/")
        self.kindlepath.set(str(a.encode(sys.getfilesystemencoding())))

root = tk.Tk()
app = App(root)
root.title('ExtractCoverThumbs ' + __version__)
root.resizable(width=tk.FALSE, height=tk.TRUE)
root.mainloop()
