#!/usr/bin/env python3
#   encoding: utf-8

# This is part of the Busker library.
# Copyright (C) 2024 D E Haynes

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from collections import defaultdict
import enum
import logging
from types import SimpleNamespace as Structure

import tkinter as tk
from tkinter import ttk

import urllib.error
import urllib.parse

import busker
from busker.history import SharedHistory
from busker.scraper import Scraper
import busker.visitor


class Host(enum.Enum):

    IPV4_LOOPBACK = "127.0.0.1"
    IPV4_NET_HOST = "0.0.0.0"
    IPV6_LOOPBACK = "::1"
    IPV6_NET_HOST = "::"


class GUI:
    pass


class Zone(SharedHistory):

    registry = defaultdict(list)

    def __init__(self, parent, name="", **kwargs):
        super().__init__(log_name=f"busker.gui.{name.lower()}", **kwargs)
        self.parent = parent
        self.name = name
        self.frame = ttk.LabelFrame(parent, text=name)

        container = defaultdict(list)
        for attr, obj in self.build(self.frame):
            container[attr].append(obj)
        self.controls = Structure(**container)

    @staticmethod
    def grid(arg, **kwargs):
        arg.grid(**kwargs)
        return arg

    @staticmethod
    def build(frame: ttk.Frame):
        return
        yield


class InfoZone(Zone):

    def __init__(self, parent, name="", **kwargs):
        super().__init__(parent, name=name, **kwargs)
        self.scraper = Scraper()
        self.reader = None

    def build(self, frame: ttk.Frame):
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=2)
        frame.columnconfigure(2, weight=1)
        frame.columnconfigure(3, weight=4)
        yield "label", self.grid(ttk.Label(frame, text="URL"), row=0, column=0, padx=(1, 1) )
        yield "entry", self.grid(ttk.Entry(frame, justify=tk.LEFT), row=0, column=1, padx=(1, 1), sticky=tk.W + tk.E)
        yield "button", self.grid(
            tk.Button(frame, text="Connect", command=self.on_connect),
            row=0, column=2, padx=(10, 10), sticky=tk.E
        )
        yield "label", self.grid(ttk.Label(frame, text="No connection to host"), row=0, column=3, padx=(1, 1))

    def on_connect(self):
        host = self.controls.entry[0].get()
        url = urllib.parse.urljoin(host, "about")
        self.reader = busker.visitor.Read(url=url)
        info = self.controls.label[1]
        try:
            node = self.reader.run(self.scraper)
        except urllib.error.URLError as e:
            info.configure(text="No connection to host")
            self.log(f"{e!s}", level=logging.WARNING)
            return

        info.configure(text=node.text.strip())


class InteractiveZone(Zone):
    pass


class PackageZone(Zone):

    def build(self, frame: ttk.Frame):
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        yield "label", self.grid(ttk.Label(frame, text="Source"), row=0, column=0, padx=(10, 10))
        yield "entry", self.grid(ttk.Entry(frame, justify=tk.LEFT, width=64), row=0, column=1, padx=(10, 10))


class ServerZone(Zone):

    def build(self, frame: ttk.Frame):
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(0, weight=5)
        frame.columnconfigure(1, weight=1)

        yield "label", self.grid(ttk.Label(frame, text="Entry point"), row=0, column=0, padx=(10, 10))
        yield "entry", self.grid(ttk.Entry(frame, justify=tk.LEFT, width=24), row=0, column=1, padx=(10, 10))

        yield "label", self.grid(ttk.Label(frame, text="Host"), row=0, column=2, padx=(10, 10))
        combo_box = ttk.Combobox(frame, justify=tk.LEFT, width=14, values=[i.value for i in Host])
        combo_box.current(0)
        yield "entry", self.grid(combo_box, row=0, column=3, padx=(10, 10))

        yield "label", self.grid(ttk.Label(frame, text="Port"), row=0, column=4, padx=(10, 10))
        spin_box = ttk.Spinbox(frame, justify=tk.LEFT, width=4, values=(80, 8000, 8001, 8080, 8081, 8082, 8088))
        spin_box.set(8080)
        yield "entry", self.grid(spin_box, row=0, column=5, padx=(10, 10))

        yield "button", self.grid(
            tk.Button(frame, text="Activate", command=self.on_activate),
            row=0, column=6, padx=(10, 10), sticky=tk.E
        )
        text_widget = tk.Text(frame)
        text_widget.insert(tk.END, "asdfghjrtyuhjk\njnion" * 150)
        scroll_bar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scroll_bar.set)
        yield "text", self.grid(text_widget, row=1, column=0, columnspan=6, padx=(10, 10), sticky=tk.E + tk.W)
        yield "scroll", self.grid(scroll_bar, row=1, column=6, pady=(10, 10), sticky=tk.N + tk.S)

    def on_activate(self):
        print(self.controls)


def build(config: dict = {}):
    root = tk.Tk()
    root.title(f"Busker {busker.__version__}")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    notebook = ttk.Notebook(root)
    notebook.grid(row=0, column=0, sticky=tk.N + tk.E + tk.S + tk.W)


    pages = [
        Structure(
            name="Playing",
            frame=tk.Frame(notebook),
            zones = []
        ),
        Structure(
            name="Hosting",
            frame=tk.Frame(notebook),
            zones = []
        ),
        Structure(
            name="Plugins",
            frame=tk.Frame(notebook),
            zones = []
        ),
    ]

    pages[0].zones.extend([
        InfoZone(pages[0].frame, name="Info"),
        InteractiveZone(pages[0].frame, name="Interactive"),
    ])
    pages[1].zones.extend([
        PackageZone(pages[1].frame, name="Package"),
        Zone(pages[1].frame, name="Environment"),
        ServerZone(pages[1].frame, name="Server"),
    ])


    for p, page in enumerate(pages):
        page.frame.grid()
        notebook.add(page.frame, text=page.name)
        if p == 0:
            page.frame.rowconfigure(0, weight=1)
            page.frame.rowconfigure(1, weight=15)
            page.frame.columnconfigure(0, weight=1)
            page.zones[0].frame.grid(row=0, column=0, padx=(2, 2), pady=(6, 1), sticky=tk.N + tk.E + tk.S + tk.W)
            page.zones[1].frame.grid(row=1, column=0, padx=(2, 2), pady=(6, 1), sticky=tk.N + tk.E + tk.S + tk.W)
            continue
        else:
            page.frame.columnconfigure(0, weight=1)

        for z, zone in enumerate(page.zones):
            page.frame.rowconfigure(z, weight=1)
            zone.frame.grid(row=z, column=0, sticky=tk.N + tk.E + tk.S + tk.W)

    root.minsize(720, 480)
    return root


if __name__ == "__main__":
    root = build()
    root.mainloop()
