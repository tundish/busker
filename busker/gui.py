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
notebook = ttk.Notebook(root)
notebook.grid()
frames = [
    tk.Frame(notebook),
    tk.Frame(notebook),
    tk.Frame(notebook),
]

for frame, title in zip(frames, ("Interactive", "Setup", "Automation")):
    # Alt - l/r cursor to cwselectswitch
    frame.grid()
    notebook.add(frame, text=title)

root.mainloop()
