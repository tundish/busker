#!/usr/bin/env python
#   encoding: utf-8

# Copyright (C) 2026 D E Haynes
# This file is part of busker.

# Busker is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# Busker is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with busker.
# If not, see <https://www.gnu.org/licenses/>.

import logging
import queue
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace as SN


def build_edit_panel(parent: tk.Widget):
    logger = logging.getLogger("edit_panel")
    rv = SN(name="Editor")
    rv.frame = ttk.Frame(parent)
    rv.frame.columnconfigure(0, weight=1)
    rv.frame.columnconfigure(1, weight=0)
    rv.frame.rowconfigure(0, weight=1)

    rv.text_widget = tk.Text(rv.frame)
    rv.text_widget.grid(row=0, column=0, sticky="NESW")
    scroll_bar = ttk.Scrollbar(rv.frame, orient=tk.VERTICAL, command=rv.text_widget.yview)
    scroll_bar.grid(row=0, column=1, sticky="NS")
    rv.text_widget.configure(yscrollcommand=scroll_bar.set)
    return rv
