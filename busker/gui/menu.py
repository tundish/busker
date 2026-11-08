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

import argparse
import asyncio
from collections.abc import Generator
import concurrent.futures
import contextvars
import dataclasses
import datetime
import functools
import itertools
import logging
import logging.handlers
import operator
import pathlib
import tempfile
import time
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from types import SimpleNamespace as Result
import queue
import sys
import weakref


import busker
from busker.model.journal import Journal
from busker.model.types import BackendType

"""
Demo of multiple threads accessing the same Journal, eg:
    + A thread running an asyncio web stack
    + A continuous mapper / design rule checker
    + A backend text console
    + A sync / backup thread

Need to manage the write lock, etc.

"""


class Scenario:
    "A manager of journals"

    instances = weakref.WeakValueDictionary()

    @classmethod
    def discover(cls, playlist_path: pathlib.Path):
        patterns = [playlist_path.glob(f"*/*{i}") for t in BackendType for i in t.value]
        resources = sorted(path for pattern in patterns for path in pattern)
        return [
            cls(parent, *children)
            for parent, children in itertools.groupby(resources, key=operator.attrgetter("parent"))
        ]

    @staticmethod
    def stats(path):
        return dict(
            mtime=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(path.stat().st_mtime)),
            size=f"{path.stat().st_size/1E3:0.3f}K" if path.is_file() else "",
        )

    def __init__(self, path: pathlib.Path, *args: tuple[Journal], **kwargs):
        # TODO: Temporary session directory?
        self.path = path
        self.args = list(args)

    def __repr__(self):
        return f"{self.path.name}@{self.path.parent.as_posix()}"

    def clone(self, name, debug=False):
        with tempfile.TemporaryDirectory(prefix="busker_", delete=not debug) as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            # TODO: get journal write locks.

    @property
    def journals(self):
        # TODO: Discover
        return self.args


class LogBridge(logging.Handler):

    def __init__(self, log_queue: queue.Queue, level=logging.NOTSET, fmt=None, defaults=None):
        super().__init__(level=level)
        self.log_queue = log_queue
        fmt = fmt or "{asctime}| {levelname:>8}| {name:<18} | {message}"
        self.setFormatter(logging.Formatter(fmt=fmt, datefmt=None, style="{", validate=True, defaults=defaults))

    def emit(self, record):
        msg = self.formatter.format(record)
        self.log_queue.put(msg, block=False)


class Controller:

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
                text = gui.log_panel.log_queue.get(block=False)
                gui.log_panel.text_widget.insert(tk.END, f"{text}\n")
                gui.log_panel.text_widget.see(tk.END)
            except queue.Empty:
                break

        gui.status_panel.clock_display.configure(text=datetime.datetime.now().strftime("%H:%M"))
        gui.root.after(150, Controller.monitor, gui)
