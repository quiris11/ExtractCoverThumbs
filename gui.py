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


__license__ = 'GNU Affero GPL v3'
__copyright__ = '2014, Robert Błaut listy@blaut.biz'
__appname__ = u'ExtractCoverThumbs'
numeric_version = (0, 7)
__version__ = u'.'.join(map(unicode, numeric_version))
__author__ = u'Robert Błaut <listy@blaut.biz>'


from ExtractCoverThumbs import extract_cover_thumbs
from Tkinter import *
from ScrolledText import ScrolledText
import tkFileDialog
import tkMessageBox
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
        self.is_azw = BooleanVar()
        self.is_log = BooleanVar()
        self.nac = IntVar()
        self.is_overwrite = BooleanVar()
        self.kindlepath = StringVar()
        self.status = StringVar()
        self.days = StringVar()

        self.frame = Frame(master, borderwidth=5)
        self.frame.pack(side=TOP, anchor=W)

        self.chk_button = Button(self.frame, text="Choose Kindle",
                                 command=self.askdirectory, width=15)
        self.chk_button.pack(side=LEFT)

        self.kindle_label = Label(self.frame, textvariable=self.kindlepath)
        self.kindle_label.pack(side=LEFT)

        self.frame2 = Frame(master, borderwidth=5)
        self.frame2.pack(side=TOP, pady=5)
        self.log_checkbox = Checkbutton(
            self.frame2, text="Write detailed informations in Message Window?",
            variable=self.is_log
        )
        self.log_checkbox.deselect()
        self.log_checkbox.pack(side=TOP, anchor=NW)

        self.apnx_checkbox = Checkbutton(
            self.frame2, text="Generate book page numbers (APNX file)?",
            variable=self.is_apnx
        )
        self.apnx_checkbox.deselect()
        self.apnx_checkbox.pack(side=TOP, anchor=NW)


        self.over_checkbox = Checkbutton(
            self.frame2,
            text="Overwrite Cover Thumbnails existing on a device?",
            variable=self.is_overwrite
        )

        self.over_checkbox.deselect()
        self.over_checkbox.pack(side=TOP, anchor=NW)

        self.azw_checkbox = Checkbutton(
            self.frame2,
            text="Extract covers from AZW files (for special needs)?",
            variable=self.is_azw
        )
        self.azw_checkbox.deselect()
        self.azw_checkbox.pack(side=TOP, anchor=NW)

        self.days_entry = Entry(
            self.frame2, width=4,
            textvariable=self.days,
            state=DISABLED
        )
        self.days_entry.pack(side=RIGHT, anchor=NW)

        self.days_checkbox = Checkbutton(
            self.frame2,
            text="Process only younger files than days provided: ",
            variable=self.nac,
            command=self.naccheck
        )
        self.days_checkbox.deselect()
        self.days_checkbox.pack(side=TOP, anchor=NW)

        self.frame3 = Frame(master, borderwidth=5)
        self.frame3.pack(side=TOP, anchor=W)

        self.run_button = Button(self.frame3, text="Start", command=self.run,
                                 width=15)
        self.run_button.pack(side=LEFT)

        self.status_label = Label(self.frame3, textvariable=self.status)
        self.status_label.pack(side=LEFT, pady=5)

        self.frame4 = Frame(master, borderwidth=5)
        self.frame4.pack(side=TOP)

        self.msg1 = 'Message Window: \n'
        self.stext = ScrolledText(self.frame4, bd=1, wrap=WORD,
                                  height=20, relief=RIDGE)
        if sys.platform == 'win32':
            self.stext.config(font=('Courier', 9, 'normal'))
        self.stext.pack()
        self.stext.insert(END, self.msg1)

        sys.stdout = StdoutRedirector(self.stext)

    def naccheck(self):
        if self.nac.get() == 0:
            self.days_entry.delete(0, END)
            self.days_entry.configure(state='disabled')
        else:
            self.days_entry.configure(state='normal')

    def run(self):
        self.docs = os.path.join(self.kindlepath.get(), 'documents')
        self.stext.delete(1.0, END)
        self.status.set('Start processing your books...')
        tkMessageBox.showwarning(
            'Starting...',
            'Process is starting. Click OK button and wait for '+
            'finish confirmation...',
            icon='question',
            parent=root
        )
        self.frame.update_idletasks()
        if self.days.get() == '':
            ec = extract_cover_thumbs(
                self.is_log.get(), self.is_overwrite.get(),
                self.is_apnx.get(), self.kindlepath.get(),
                self.docs, self.is_azw, None
            )
        else:
            ec = extract_cover_thumbs(
                self.is_log.get(), self.is_overwrite.get(),
                self.is_apnx.get(), self.kindlepath.get(),
                self.docs, self.is_azw, self.days.get()
            )
        if ec == 0:
            self.status.set('Process finished.')
            tkMessageBox.showwarning(
                'Finished...',
                'Process finished. Check Message Window for details...',
                icon='info',
                parent=root
            )
        elif ec == 1:
            self.status.set('Process finished with PROBLEMS!')
            tkMessageBox.showwarning(
                'Finished...',
                'Process finished with PROBLEMS! ' +
                'Check Message Window for details...' ,
                icon='warning',
                parent=root
            )

    def askdirectory(self):
        if sys.platform == 'win32':
            a = tkFileDialog.askdirectory(initialdir="c:/")
        else:
            a = tkFileDialog.askdirectory(initialdir="/")
        self.kindlepath.set(str(a.encode(sys.getfilesystemencoding())))

root = Tk()
app = App(root)
root.title('ExtractCoverThumbs ' + __version__)
root.resizable(width=FALSE, height=FALSE)
root.mainloop()
