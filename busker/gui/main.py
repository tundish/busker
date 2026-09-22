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


def build_tree_panel(parent: tk.Widget):
    logger = logging.getLogger("tree_panel")
    rv = Result()
    style = ttk.Style()
    family = next(iter({"Courier New", "Liberation Mono", "Ubuntu Mono"}.intersection(set(tkfont.families()))))
    logger.info(f"Selected font family '{family}'")
    fonts = [
        tkfont.Font(family=family, size=12, weight="bold"),
        tkfont.Font(family=family, size=12, weight="normal"),
    ]
    style.configure("Treeview.Heading", font=fonts[0].actual(), rowheight=24)
    style.configure("Treeview", font=fonts[1].actual(), rowheight=24)
    rv.frame = ttk.Frame(parent)
    rv.frame.columnconfigure(0, weight=1)
    rv.frame.columnconfigure(1, weight=0)
    rv.frame.rowconfigure(0, weight=1)

    def on_select(event=None):
        logger.info(f"selected {event}")

    rv.tree_widget = ttk.Treeview(rv.frame, show="tree headings", columns=("size", "modified"))
    rv.tree_widget["columns"] = ("size", "saved")
    rv.tree_widget.column("#0", minwidth=fonts[0].measure("0" * 36))
    rv.tree_widget.column("#1", minwidth=fonts[0].measure("0" * 20))
    rv.tree_widget.column("#2", minwidth=fonts[0].measure("0" * 6))
    rv.tree_widget.grid(row=0, column=0, sticky="NESW")
    scroll_bar = ttk.Scrollbar(rv.frame, orient=tk.VERTICAL, command=rv.tree_widget.yview)
    scroll_bar.grid(row=0, column=1, sticky="NS")
    rv.tree_widget.configure(yscrollcommand=scroll_bar.set, selectmode="browse")
    rv.tree_widget.bind('<<TreeviewSelect>>', on_select)
    return rv


def build_context_menus(parent: tk.Widget):
    logger = logging.getLogger("context_menu")
    rv = Result()
    rv.menus = [
        tk.Menu(parent, tearoff=0, takefocus=1)
    ]

    rv.menus[0].add_command(label="Cut")
    rv.menus[0].add_command(label="Copy")
    rv.menus[0].add_command(label="Paste")
    rv.menus[0].add_command(label="Reload", underline=1, accelerator="Ctrl+R")
    rv.menus[0].add_separator()
    rv.menus[0].add_command(label ="Rename")
    parent.bind(
        "<Button-3>",
        functools.partial(Controller.select_tree_item, gui=rv, parent=parent)
    )
    parent.bind(
        "<ButtonRelease-3>",
        functools.partial(Controller.display_tree_item_context_menu, gui=rv, parent=parent)
    )
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
    rv.frame.columnconfigure(1, weight=0)
    rv.frame.columnconfigure(2, weight=0)
    ttk.Sizegrip(rv.frame).grid(row=0, column=2, sticky="SE")
    rv.clock_display = ttk.Label(rv.frame)
    rv.clock_display.grid(row=0, column=1, padx=6, pady=3, sticky="SE")
    return rv


def build_content(tree: tk.Widget, path=None):
    logger = logging.getLogger("build_content")
    rv = Result()
    rv.content = Scenario.discover(path)
    logger.info(rv.content)
    for s in rv.content:
        try:
            s_iid = tree.insert("", "end", repr(s), text=repr(s), values=[i or "" for i in s.stats(s.path).values()])
        except tk.TclError as err:
            logger.warning(err)
        for n, j in enumerate(s.journals):
            j_iid = tree.insert(s_iid, "end", j.name, text=j.name, values=[i or "" for i in s.stats(j).values()])

    return rv


def build_main_menu(parent: tk.Widget):
    logger = logging.getLogger("main_menu")
    rv = Result()
    rv.menu = tk.Menu(parent, tearoff=0, takefocus=1)

    def on_select(event=None):
        logger.info(f"selected {event}")

    rv.menu.add_command(label="File", underline=0)
    rv.menu.add_command(label="Edit", underline=0)
    rv.menu.add_command(label="Help", underline=0)
    # rv.menu.add_command(label="Reload", underline=0, accelerator="Ctrl+R", command=on_select)
    # parent.bind("<Button-3>", do_popup)
    # parent.bind('<ButtonRelease-3>', do_popup)
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

    # root.configure(menu=menubar)
    # https://tkdocs.com/tutorial/menus.html
    rv.context_menus = build_context_menus(rv.tree_panel.tree_widget)
    rv.content = build_content(rv.tree_panel.tree_widget, path=args.playlist)

    book = ttk.Notebook(base_split)
    base_split.add(book)

    rv.log_panel = build_log_panel(base_split)
    book.add(rv.log_panel.frame, text=rv.log_panel.name)
    rv.status_panel = build_status_panel(base)
    rv.status_panel.frame.grid(row=1, column=0, sticky="NESW")

    rv.main_menu = build_main_menu(base)
    rv.root.configure(menu=rv.main_menu.menu)
    base.grid(row=0, column=0, sticky="NESW")
    rv.root.grid()

    rv.root.after(500, Controller.monitor, rv)
    return rv


def start():
    pass


def main(args):
    args.playlist.mkdir(parents=True, exist_ok=True)
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
    rv.add_argument(
        "--playlist", type=pathlib.Path,
        default=(default := pathlib.Path.home().joinpath("busker_playlist").resolve()),
        help=f"Specify a playlist location [{default}]"
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
