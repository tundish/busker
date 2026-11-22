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

class Message:
    """
        `serial`
        : The serial number of the event.
        `num`
        : The mouse button that was pressed or released (for button events).
        `focus`
        : Whether the window has the focus (for Enter and Leave events).
        `height`
        : The new height of the window (for Configure and Expose events).
        `width`
        : The new height and width of the window (for Configure and Expose events).
        `keycode`
        : The keycode of the key that was pressed or released.
        `state`
        : The state of the event, as a number (for most events) or a string (for Visibility events).
        `time`
        : The timestamp of the event, in milliseconds.
        `x, y`
        : The pointer position relative to the widget, in pixels.
        `x_root, y_root`
        : The pointer position relative to the top-left corner of the screen, in pixels.
        `char`
        : The character typed, as a string (for key events).
        `send_event`
        : True if the event was sent by another application.
        `keysym`
        : The symbolic name of the key that was pressed or released.
        `keysym_num`
        : The numeric value of keysym.
        `type`
        : The EventType of the event.
        `widget`
        : The widget on which the event occurred.
        `delta`
        : The amount the mouse wheel was rotated (for MouseWheel events)
    """

class Clerk:
    """
    Provides validation and logical consistency.
    Only loosely bound to a GUI.

    """

    def __init__(self, root):
        self.root = root
        self.messages = dict()

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


    def register(self, new_evt, callable_):
        def fn(evt: tk.Event):
            pass
        # tk.EventType
        self.root.event_add(f"<<{new_evt}>>", "<Button-3>", "<KeyPress>")
        self.root.bind(f"<<{new_evt}>>", callable_)  # Or wrap callable?
        rv = self.root.event_info(f"<<{new_evt}>>")
        return False

    def dispatch(self, evt):
        self.root.event_generate(tk_evt, **kwargs)
