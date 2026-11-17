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
from tkinter import font as tkfont
from types import SimpleNamespace as SN



def build_outline_panel(parent: tk.Widget):
    logger = logging.getLogger("ouline_panel")
    rv = SN()
    style = ttk.Style()
    rv.frame = ttk.Frame(parent)
    rv.frame.columnconfigure(0, weight=1)
    rv.frame.columnconfigure(1, weight=0)
    rv.frame.rowconfigure(0, weight=1)

    def on_select(event=None):
        logger.debug(f"selected {event}")

    rv.tree_wgt = ttk.Treeview(rv.frame, show="tree headings", columns=("pos", "end"))
    rv.tree_wgt["columns"] = ("pos", "pos")
    # rv.tree_wgt.column("#0", minwidth=fonts[0].measure("0" * 36))
    # rv.tree_wgt.column("#1", minwidth=fonts[0].measure("0" * 20))
    # rv.tree_wgt.column("#2", minwidth=fonts[0].measure("0" * 6))
    rv.tree_wgt.grid(row=0, column=0, sticky="NESW")
    scroll_bar = ttk.Scrollbar(rv.frame, orient=tk.VERTICAL, command=rv.tree_wgt.yview)
    scroll_bar.grid(row=0, column=1, sticky="NS")
    rv.tree_wgt.configure(yscrollcommand=scroll_bar.set, selectmode="browse")
    rv.tree_wgt.bind('<<TreeviewSelect>>', on_select)
    return rv


def build_edit_panel(parent: tk.Widget):
    logger = logging.getLogger("edit_panel")
    rv = SN(name="Editor")
    rv.split = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
    rv.split.grid(row=0, column=0, sticky="NESW")

    rv.outline_pnl = build_outline_panel(rv.split)
    rv.split.add(rv.outline_pnl.frame, weight=0)
    # rv.outline_pnl.frame.grid(row=0, column=0, sticky="NESW")

    rv.frame = ttk.Frame(rv.split)
    rv.frame.columnconfigure(0, weight=1)
    rv.frame.columnconfigure(1, weight=0)
    rv.frame.rowconfigure(0, weight=1)
    rv.split.add(rv.frame, weight=1)
    # rv.frame.grid(row=0, column=1, sticky="NESW")

    rv.text_wgt = tk.Text(rv.frame)
    rv.text_wgt.grid(row=0, column=0, sticky="NESW")
    scroll_bar = ttk.Scrollbar(rv.frame, orient=tk.VERTICAL, command=rv.text_wgt.yview)
    scroll_bar.grid(row=0, column=1, sticky="NS")
    rv.text_wgt.configure(yscrollcommand=scroll_bar.set)
    return rv
