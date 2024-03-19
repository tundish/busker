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

import tkinter as tk
from tkinter import ttk

import busker


class GUI:
    pass


root = tk.Tk()
root.title(f"Busker {busker.__version__}")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

notebook = ttk.Notebook(root)
notebook.grid(row=0, column=0, sticky=tk.N + tk.E + tk.S + tk.W)

pages = [
    tk.Frame(notebook),
    tk.Frame(notebook),
    tk.Frame(notebook),
]

zones = [
    ttk.LabelFrame(pages[1], text="Package"),
    ttk.LabelFrame(pages[1], text="Environment"),
]

for page, title in zip(pages, ("Interactive", "Setup", "Automation")):
    # Alt - l/r cursor to cwselectswitch
    page.grid()
    notebook.add(page, text=title)

for zone in zones:
    zone.grid()

label = ttk.Label(zones[0], text="Test")
label.grid(row=0, column=0, sticky=tk.W, padx=(10, 10))
root.minsize(720, 480)
root.mainloop()
