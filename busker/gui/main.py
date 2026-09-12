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
import logging
import pathlib
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace as Result
import queue
import sys
import weakref


import busker
from busker.model.journal import Journal

"""
Demo of multiple threads accessing the same Journal, eg:
    + A thread running an asyncio web stack
    + A continuous mapper / design rule checker
    + A backend text console
    + A sync / backup thread

Need to manage the write lock, etc.

"""

"""
        tree = ttk.Treeview(parent)
        tree["columns"] = Scenario._fields[1:]
        for c in tree["columns"]:
            tree.heading(c, text=c.title())
            tree.column(c, width=32)

        tree.grid(column=0, row=0, sticky="NESW")

    def add_item(self, name, data:dict):
        if name:
            item = Scenario(name, *data.values())
            try:
                tree.insert("", "end", item.name, text=item.name, values=item[1:])
            except tk.TclError:
                pass

    def delete_item(self):
        item = tree.selection()
        try:
            stree.delete(item)
        except tk.TclError:
            pass

    def get_items(self, *args):
        return [
            Scenario(i["text"], *i["values"])
            for i in [tree.item(i) for i in tree.get_children()]
        ]

"""

class Scenario:
    "A manager of journals"

    instances = weakref.WeakValueDictionary()

    def __init__(self):
        self.journals = []


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


class LogBridge(logging.Handler):

    def __init__(self, log_queue: queue.Queue, level=logging.NOTSET, fmt=None, defaults=None):
        super().__init__(level=level)
        self.log_queue = log_queue
        fmt = fmt or "{asctime}| {levelname:>8}| {name:<18} | {message}"
        self.setFormatter(logging.Formatter(fmt=fmt, datefmt=None, style="{", validate=True, defaults=defaults))

    def emit(self, record):
        msg = self.formatter.format(record)
        self.log_queue.put(msg, block=False)


def monitor(gui):
    logger = logging.getLogger("monitor")

    while True:
        try:
            text = gui.log_panel.log_queue.get(block=False)
            gui.log_panel.text_widget.insert(tk.END, f"{text}\n")
            gui.log_panel.text_widget.see(tk.END)
        except queue.Empty:
            break

    gui.root.after(150, monitor, gui)


def build_tree_panel(parent: tk.Widget):
    logger = logging.getLogger("tree_panel")
    rv = Result()
    rv.frame = ttk.Frame(parent)
    rv.frame.columnconfigure(0, weight=1)
    rv.frame.columnconfigure(1, weight=0)
    rv.frame.rowconfigure(0, weight=1)

    rv.tree_widget = ttk.Treeview(rv.frame)
    rv.tree_widget.grid(row=0, column=0, sticky="NESW")
    scroll_bar = ttk.Scrollbar(rv.frame, orient=tk.VERTICAL, command=rv.tree_widget.yview)
    scroll_bar.grid(row=0, column=1, sticky="NS")
    rv.tree_widget.configure(yscrollcommand=scroll_bar.set, selectmode="browse")
    return rv


def build_context_menu(parent: tk.Widget):
    logger = logging.getLogger("context_menu")
    rv = Result()
    rv.menu = tk.Menu(parent, tearoff=0, takefocus=1)

    def on_select(event=None):
        logger.info(f"selected {event}")

    def do_popup(event):
        item = parent.selection()
        logger.info(f"{item=}")
        try:
            logger.info(event)
            rv.menu.tk_popup(event.x_root, event.y_root)
        finally:
            rv.menu.grab_release()

    rv.menu.add_command(label="Cut")
    rv.menu.add_command(label="Copy")
    rv.menu.add_command(label="Paste")
    rv.menu.add_command(label="Reload", underline=1, accelerator="Ctrl+R", command=on_select)
    rv.menu.add_separator()
    rv.menu.add_command(label ="Rename")
    parent.bind("<Button-3>", do_popup)
    return rv


def build_log_panel(parent: tk.Widget):
    logger = logging.getLogger("log_panel")
    rv = Result(name="Log")
    rv.frame = ttk.Frame(parent)
    rv.frame.columnconfigure(0, weight=1)
    rv.frame.columnconfigure(1, weight=0)
    rv.frame.rowconfigure(0, weight=1)

    rv.text_widget = tk.Text(rv.frame)
    rv.text_widget.grid(row=0, column=0, sticky="NESW")
    scroll_bar = ttk.Scrollbar(rv.frame, orient=tk.VERTICAL, command=rv.text_widget.yview)
    scroll_bar.grid(row=0, column=1, sticky="NS")
    rv.text_widget.configure(yscrollcommand=scroll_bar.set)

    rv.log_queue = queue.Queue()
    logging.getLogger().addHandler(LogBridge(rv.log_queue))
    parent.after(500, logger.info(f"Busker {busker.__version__}"))
    return rv


def build_status_panel(parent: tk.Widget):
    rv = Result()
    rv.frame = ttk.Frame(parent)
    rv.frame.rowconfigure(0, weight=1)
    rv.frame.columnconfigure(0, weight=1)
    rv.frame.columnconfigure(1, weight=1)
    rv.frame.columnconfigure(2, weight=0)
    ttk.Sizegrip(rv.frame).grid(row=0, column=2, sticky="SE")
    return rv


def build_gui(args: argparse.Namespace):
    rv = Result()
    rv.root = tk.Tk()
    rv.root.title(f"Busker {busker.__version__}")
    rv.root.columnconfigure(0, weight=1)
    rv.root.rowconfigure(0, weight=1)

    base = ttk.Frame(rv.root)
    base.columnconfigure(0, weight=1)
    base.rowconfigure(0, weight=1)
    base.rowconfigure(1, weight=0)

    base_split = ttk.PanedWindow(base, orient=tk.HORIZONTAL)
    base_split.grid(row=0, column=0, sticky="NESW")

    rv.tree_panel = build_tree_panel(base_split)
    base_split.add(rv.tree_panel.frame)

    rv.context_menu = build_context_menu(rv.tree_panel.tree_widget)

    book = ttk.Notebook(base_split)
    base_split.add(book)

    rv.log_panel = build_log_panel(base_split)
    book.add(rv.log_panel.frame, text=rv.log_panel.name)
    rv.status_panel = build_status_panel(base)
    rv.status_panel.frame.grid(row=1, column=0, sticky="NESW")

    base.grid(row=0, column=0, sticky="NESW")
    rv.root.grid()

    rv.root.after(500, monitor, rv)
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
