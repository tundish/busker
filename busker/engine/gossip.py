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
import logging
import pathlib
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace as Gift
import queue
import sys


import busker

"""
Demo of multiple threads accessing the same Journal, eg:
    + A thread running an asyncio web stack
    + A continuous mapper / design rule checker
    + A backend text console
    + A sync / backup thread

Need to manage the write lock, etc.

"""

class LogBridge(logging.Handler):

    def __init__(self, log_queue: queue.Queue, level=logging.NOTSET, fmt=None, defaults=None):
        super().__init__(level=level)
        self.log_queue = log_queue
        fmt = fmt or "{asctime}| {levelname:>8}| {name:<18} | {message}"
        self.setFormatter(logging.Formatter(fmt=fmt, datefmt=None, style="{", validate=True, defaults=defaults))

    def emit(self, record):
        msg = self.formatter.format(record)
        self.log_queue.put(msg, block=False)


class Resident:
    "A core-resident actor"

    # Shared among subclasses within the same thread
    shared = contextvars.ContextVar("shared")

    def __init__(self, cmd_queue: asyncio.Queue() = None, msg_queue: asyncio.Queue() = None):
        self.cmd_queue = cmd_queue or asyncio.Queue()
        self.msg_queue = msg_queue or asyncio.Queue()

    def __iter__(Self):
        "Or is __aiter__ a better fit?"
        return
        yield

    async def __aiter__(self):
        "async for i in ... means client code must be async too."
        for n in range(10):
            await asyncio.sleep(0.5)
            yield n

    async def __call__(self, **kwargs):
        async with asyncio.TaskGroup() as tasks:
            ...


def monitor(gui):
    logger = logging.getLogger("monitor")

    while True:
        try:
            text = gui.log_panel.log_queue.get(block=False)
            gui.log_panel.text_widget.insert(tk.END, text)
            gui.log_panel.text_widget.see(tk.END)
        except queue.Empty:
            break

    gui.root.after(150, monitor, gui)


def build_log_panel(parent: tk.Widget):
    logger = logging.getLogger("log_panel")
    rv = Gift()
    rv.frame = ttk.Frame(parent)
    rv.frame.columnconfigure(0, weight=1)
    rv.frame.rowconfigure(0, weight=1)

    rv.text_widget = tk.Text(parent)
    rv.text_widget.grid(row=0, column=0, sticky="NESW")
    rv.log_queue = queue.Queue()

    logging.getLogger().addHandler(LogBridge(rv.log_queue))
    parent.after(500, logger.info(f"Busker {busker.__version__}"))
    return rv


def build_gui(args: argparse.Namespace):
    rv = Gift()
    rv.root = tk.Tk()
    rv.root.title(f"Busker {busker.__version__}")
    rv.root.columnconfigure(0, weight=1)
    rv.root.rowconfigure(0, weight=1)

    rv.log_panel = build_log_panel(rv.root)
    rv.root.after(500, monitor, rv)
    rv.root.grid()
    return rv


def start():
    pass


def main(args):
    gui = build_gui(args)
    gui.root.mainloop()
    return 0


def parser():
    rv = argparse.ArgumentParser(usage=__doc__, fromfile_prefix_chars="=")
    rv.convert_arg_line_to_args = lambda x: x.split()
    rv.add_argument(
        "--debug", action="store_true", default=False,
        help=f"Display debug logs"
    )
    return rv


def run():
    p = parser()
    args = p.parse_args()
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        format="{asctime}| {levelname:>8}| {name:<18} | {message}",
        datefmt="",
        style="{",
        stream=sys.stderr,
        level=level,
    )
    rv = main(args)
    sys.exit(rv)


if __name__ == "__main__":
    run()
