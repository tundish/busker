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
from types import SimpleNamespace as Structure
import tkinter as tk
from tkinter import ttk

import busker


class Host(enum.Enum):

    IPV4_LOOPBACK = "127.0.0.1"
    IPV4_NET_HOST = "0.0.0.0"
    IPV6_LOOPBACK = "::1"
    IPV6_NET_HOST = "::"


class GUI:
    pass


class Zone:

    registry = defaultdict(list)

    def __init__(self, parent, name="", **kwargs):
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


class InfoZone(Zone):
    pass


root = tk.Tk()
root.title(f"Busker {busker.__version__}")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

notebook = ttk.Notebook(root)
notebook.grid(row=0, column=0, sticky=tk.N + tk.E + tk.S + tk.W)


pages = [
    Structure(
        name="Interactive",
        frame=tk.Frame(notebook),
        zones = []
    ),
    Structure(
        name="Setup",
        frame=tk.Frame(notebook),
        zones = []
    ),
    Structure(
        name="Automation",
        frame=tk.Frame(notebook),
        zones = []
    ),
]

pages[1].zones.extend([
    PackageZone(pages[1].frame, name="Package"),
    Zone(pages[1].frame, name="Environment"),
    ServerZone(pages[1].frame, name="Server"),
    InfoZone(pages[1].frame, name="Info"),
])


for page in pages:
    # Alt - l/r cursor to cwselectswitch
    page.frame.grid()
    page.frame.columnconfigure(0, weight=1)
    notebook.add(page.frame, text=page.name)

    for n, zone in enumerate(page.zones):
        page.frame.rowconfigure(n, weight=1)
        zone.frame.grid(row=n, column=0, sticky=tk.N + tk.E + tk.S + tk.W)

root.minsize(720, 480)
root.mainloop()
