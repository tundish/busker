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

from types import SimpleNamespace as Structure
import tkinter as tk
from tkinter import ttk

import busker


class GUI:
    pass


class Zone:

    def __init__(self, parent, name="", **kwargs):
        self.parent = parent
        self.frame = ttk.LabelFrame(parent, text=name)

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
    ttk.LabelFrame(pages[1].frame, text="Package"),
    ttk.LabelFrame(pages[1].frame, text="Environment"),
    ttk.LabelFrame(pages[1].frame, text="Server"),
    ttk.LabelFrame(pages[1].frame, text="Session"),
])


for page in pages:
    # Alt - l/r cursor to cwselectswitch
    page.frame.grid()
    page.frame.columnconfigure(0, weight=1)
    notebook.add(page.frame, text=page.name)

    for n, zone in enumerate(page.zones):
        page.frame.rowconfigure(n, weight=1)
        zone.grid(row=n, column=0, sticky=tk.N + tk.E + tk.S + tk.W)

# label = ttk.Label(zones[0], text="Test")
# label.grid(row=0, column=0, sticky=tk.W, padx=(10, 10))
root.minsize(720, 480)
root.mainloop()
