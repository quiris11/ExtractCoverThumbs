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


from Tkinter import *
import tkFileDialog


class App:

    def __init__(self, master):
        self.apnx = BooleanVar()
        self.overwrite = BooleanVar()
        self.v = StringVar()
        self.bla = str(self.apnx) + 'bla'
        frame = Frame(master)
        frame.pack()

        self.hi_there = Button(frame, text="Choose Kindle",
                               command=self.askdirectory)
        self.hi_there.pack(side=TOP, fill=X)

        self.w = Label(master, textvariable=self.v)
        self.w.pack(side=TOP, anchor=W)

        self.a = Checkbutton(frame, text="Generate APNX?", variable=self.apnx)
        self.a.deselect()
        self.a.pack(side=TOP, anchor=W)

        self.o = Checkbutton(frame, text="Overwrite Cover Thumbs?",
                             variable=self.overwrite)
        self.o.deselect()
        self.o.pack(side=TOP, anchor=W)

        self.w = Label(master, textvariable=self.v)
        self.w.pack(side=TOP, anchor=W)

        # self.quit = Button(frame, text="Quit", command=frame.quit)
        # self.quit.pack(side=TOP)

        self.hi_there = Button(frame, text="Run process", command=self.run)
        self.hi_there.pack(side=TOP, fill=X)

    def run(self):
        # self.v.set('bbbbbb')
        self.v.set(str(self.apnx.get()) + ' ' + str(self.overwrite.get()))

    def askdirectory(self):
        a = tkFileDialog.askdirectory()
        self.v.set(str(a))

root = Tk()
app = App(root)
root.title('ExtractCoverThumbs 0.6')
root.mainloop()
