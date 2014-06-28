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
import tkFileDialog
import sys
import os


class App:

    def __init__(self, master):
        self.is_apnx = BooleanVar()
        self.is_log = BooleanVar()
        self.is_overwrite = BooleanVar()
        self.kindlepath = StringVar()
        self.status = StringVar()

        frame = Frame(master, borderwidth=20)
        frame.pack()

        self.chk_button = Button(frame, text="Choose Kindle",
                                 command=self.askdirectory)
        self.chk_button.pack(side=TOP, fill=X)

        self.kindle_label = Label(frame, textvariable=self.kindlepath)
        self.kindle_label.pack(side=TOP, pady=5)

        self.apnx_checkbox = Checkbutton(frame, text="Generate APNX?",
                                         variable=self.is_apnx)
        self.apnx_checkbox.select()
        self.apnx_checkbox.pack(side=TOP, anchor=W)

        self.log_checkbox = Checkbutton(frame, text="Generate Log File?",
                                        variable=self.is_log)
        self.log_checkbox.deselect()
        self.log_checkbox.pack(side=TOP, anchor=W)

        self.over_checkbox = Checkbutton(frame, text="Overwrite Cover Thumbs?",
                                         variable=self.is_overwrite)
        self.over_checkbox.deselect()
        self.over_checkbox.pack(side=TOP, anchor=W)

        self.empty = Label(frame, width=30)
        self.empty.pack(side=TOP, anchor=W)

        self.run_button = Button(frame, text="Start", command=self.run)
        self.run_button.pack(side=TOP, fill=X)

        self.w = Label(frame, textvariable=self.status)
        self.w.pack(side=TOP, pady=5)

        self.show_log_button = Button(frame, text="Open Log File",
                                      command=self.run)
        self.show_log_button.pack(side=TOP, fill=X)

    def run(self):
        self.docs = os.path.join(self.kindlepath.get(), 'documents')
        self.status.set('Start processing...')
        extract_cover_thumbs(self.is_log.get(), self.is_overwrite.get(),
                             self.is_apnx.get(), self.kindlepath.get(),
                             self.docs)
        self.status.set('Process finished...')

    def askdirectory(self):
        a = tkFileDialog.askdirectory()
        self.kindlepath.set(str(a.encode(sys.getfilesystemencoding())))

root = Tk()
app = App(root)
root.title('ExtractCoverThumbs 0.6')
# root.geometry("280x250+50+50")
root.mainloop()
