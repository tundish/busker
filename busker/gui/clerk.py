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

import datetime
from functools import partial
import logging

import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

from types import SimpleNamespace as SN
import queue


class Clerk:
    """
    Provides validation and logical consistency.
    Only loosely bound to a GUI.

    """

    @staticmethod
    def select_tree_item(event=None, gui=None, parent=None):
        logger = logging.getLogger("context_menu")
        logger.info(f"{parent=} {event=}")
        row = parent.identify_row(event.y)
        parent.selection_set(row)
        iid = parent.selection()
        text = parent.item(iid, "text")
        logger.info(f"selected {iid=} {text=}")

    @staticmethod
    def display_tree_item_context_menu(event=None, gui=None, parent=None):
        logger = logging.getLogger("context_menu")
        row = parent.identify_row(event.y)
        parent.selection_set(row)
        logger.info(f"{row=}")
        # TODO: Pick the menu here.
        try:
            logger.info(event)
            gui.menus[0].tk_popup(event.x_root, event.y_root)
        finally:
            gui.menus[0].grab_release()

    @staticmethod
    def monitor(gui):
        logger = logging.getLogger("monitor")

        while True:
            try:
                text = gui.log_pnl.log_queue.get(block=False)
                gui.log_pnl.text_wgt.insert(tk.END, f"{text}\n")
                gui.log_pnl.text_wgt.see(tk.END)
            except queue.Empty:
                break

        gui.status_pnl.clock_display.configure(text=datetime.datetime.now().strftime("%H:%M"))
        gui.root.after(150, Clerk.monitor, gui)


    def set_global_font(self, font: Font = None):
        logger = logging.getLogger("set_global_font")
        logger.info(font)
