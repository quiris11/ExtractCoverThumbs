#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of ExtractCoverThumbs, licensed under
# GNU Affero GPLv3 or later.
# Copyright © Robert Błaut. See NOTICE for more information.
#
# This is script extracts missing Cover Thumbnails from eBooks downloaded
# from Amazon Personal Documents Service and side loads them
# to your Kindle Paperwhite.
#

from ExtractCoverThumbs import extract_cover_thumbs
from Tkinter import *
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
                self.stext.insert(END, str)

        self.is_apnx = BooleanVar()
        self.is_log = BooleanVar()
        self.is_overwrite = BooleanVar()
        self.kindlepath = StringVar()
        self.status = StringVar()

        self.frame = Frame(master, borderwidth=20)
        self.frame.pack()

        self.chk_button = Button(self.frame, text="Choose Kindle",
                                 command=self.askdirectory)
        self.chk_button.pack(side=TOP)

        self.kindle_label = Label(self.frame, textvariable=self.kindlepath)
        self.kindle_label.pack(side=TOP, pady=5)

        self.log_checkbox = Checkbutton(self.frame, text="Detailed info?",
                                        variable=self.is_log)
        self.log_checkbox.select()
        self.log_checkbox.pack(side=TOP, anchor=W)

        self.apnx_checkbox = Checkbutton(self.frame, text="Generate APNX?",
                                         variable=self.is_apnx)
        self.apnx_checkbox.select()
        self.apnx_checkbox.pack(side=TOP, anchor=W)

        self.over_checkbox = Checkbutton(self.frame,
                                         text="Overwrite Cover Thumbs?",
                                         variable=self.is_overwrite)
        self.over_checkbox.deselect()
        self.over_checkbox.pack(side=TOP, anchor=W)

        self.empty = Label(self.frame, width=30)
        self.empty.pack(side=TOP, anchor=W)

        self.run_button = Button(self.frame, text="Start", command=self.run)
        self.run_button.pack(side=TOP)

        self.status_label = Label(self.frame, textvariable=self.status)
        self.status_label.pack(side=TOP, pady=5)

        msg1 = 'Message Log: \n'
        self.stext = ScrolledText(self.frame, bd=1, wrap=WORD, relief=RIDGE)
        self.stext.pack()
        self.stext.insert(END, msg1)

        sys.stdout = StdoutRedirector(self.stext)

    def run(self):
        self.docs = os.path.join(self.kindlepath.get(), 'documents')
        self.status.set('Start processing your books...')
        self.frame.update_idletasks()
        ec = extract_cover_thumbs(self.is_log.get(), self.is_overwrite.get(),
                                  self.is_apnx.get(), self.kindlepath.get(),
                                  self.docs)
        if ec == 0:
            self.status.set('Finished :)')
        elif ec == 1:
            self.status.set('Finished with problems!')

    def askdirectory(self):
        a = tkFileDialog.askdirectory()
        self.kindlepath.set(str(a.encode(sys.getfilesystemencoding())))

root = Tk()
app = App(root)
root.title('ExtractCoverThumbs 0.6')
root.mainloop()
