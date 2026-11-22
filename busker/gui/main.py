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
import datetime
from functools import partial
import logging
import pathlib
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
try:
    from tkinter.fontchooser import FontChooser
except ModuleNotFoundError:
    # < 3.16
    FontChooser = None

from types import SimpleNamespace as SN
import queue
import sys


import busker
from busker.gui.edit import build_edit_panel
from busker.gui.clerk import Clerk
from busker.gui.menu import LogBridge
from busker.gui.menu import Scenario
from busker.gui.theme import Theme

from busker.model.types import BackendType


"""
Demo of multiple threads accessing the same Journal, eg:
    + A thread running an asyncio web stack
    + A continuous mapper / design rule checker
    + A backend text console
    + A sync / backup thread

Need to manage the write lock, etc.

"""


def build_tree_panel(parent: tk.Widget):
    logger = logging.getLogger("tree_panel")
    rv = SN()
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
        logger.debug(f"selected {event}")

    rv.tree_wgt = ttk.Treeview(rv.frame, show="tree headings", columns=("size", "modified"))
    rv.tree_wgt["columns"] = ("size", "saved")
    rv.tree_wgt.column("#0", minwidth=fonts[0].measure("0" * 36))
    rv.tree_wgt.column("#1", minwidth=fonts[0].measure("0" * 20))
    rv.tree_wgt.column("#2", minwidth=fonts[0].measure("0" * 6))
    rv.tree_wgt.grid(row=0, column=0, sticky="NESW")
    scroll_bar = ttk.Scrollbar(rv.frame, orient=tk.VERTICAL, command=rv.tree_wgt.yview)
    scroll_bar.grid(row=0, column=1, sticky="NS")
    rv.tree_wgt.configure(yscrollcommand=scroll_bar.set, selectmode="browse")
    rv.tree_wgt.bind('<<TreeviewSelect>>', on_select)
    return rv


def build_context_menus(parent: tk.Widget):
    logger = logging.getLogger("context_menu")
    rv = SN()
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
        partial(Clerk.select_tree_item, gui=rv, parent=parent)
    )
    parent.bind(
        "<ButtonRelease-3>",
        partial(Clerk.display_tree_item_context_menu, gui=rv, parent=parent)
    )
    return rv


def build_log_panel(parent: tk.Widget):
    logger = logging.getLogger("log_panel")
    rv = SN(name="Log")
    rv.frame = ttk.Frame(parent)
    rv.frame.columnconfigure(0, weight=1)
    rv.frame.columnconfigure(1, weight=0)
    rv.frame.rowconfigure(0, weight=1)

    rv.text_wgt = tk.Text(rv.frame)
    rv.text_wgt.grid(row=0, column=0, sticky="NESW")
    scroll_bar = ttk.Scrollbar(rv.frame, orient=tk.VERTICAL, command=rv.text_wgt.yview)
    scroll_bar.grid(row=0, column=1, sticky="NS")
    rv.text_wgt.configure(yscrollcommand=scroll_bar.set)

    rv.log_queue = queue.Queue()
    logging.getLogger().addHandler(LogBridge(rv.log_queue))
    parent.after(500, logger.info(f"Busker {busker.__version__}"))
    return rv


def build_status_panel(parent: tk.Widget):
    rv = SN()
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
    rv = SN()
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


def build_main_menu(parent: tk.Widget, gui: SN = None):
    logger = logging.getLogger("main_menu")
    rv = SN()
    rv.menu = tk.Menu(parent, tearoff=0, takefocus=1)

    def on_select(event=None):
        logger.info(f"selected {event}")

    rv.menu.add_command(label="File", underline=0)

    view_menu = tk.Menu(parent)
    rv.menu.add_cascade(menu=view_menu, label="View", underline=0)

    theme_menu = tk.Menu(master=view_menu, tearoff=False)
    view_menu.add_cascade(menu=theme_menu, label="Theme", underline=0)
    theme_mode_var = tk.BooleanVar(master=theme_menu)
    theme_name_var = tk.StringVar(master=theme_menu)
    theme_menu.add_checkbutton(label="Dark mode", var=theme_mode_var)
    for theme_name in gui.theme.theme_names:
        theme_menu.add_radiobutton(label=theme_name, var=theme_name_var)

    if FontChooser is not None:  # FIXME: Do in Theme
        gui.theme.font_chooser = FontChooser(title="Global Font", command=gui.theme.set_global_font)
        theme_menu.add_command(label="Fonts...", underline=0, command=gui.theme.font_chooser.show)

    rv.menu.add_command(label="Help", underline=0)
    # rv.menu.add_command(label="Reload", underline=0, accelerator="Ctrl+R", command=on_select)
    # parent.bind("<Button-3>", do_popup)
    # parent.bind('<ButtonRelease-3>', do_popup)
    return rv


def build_gui(args: argparse.Namespace):
    rv = SN(root=(root:=tk.Tk()), clerk=Clerk(root), theme=Theme(root))
    rv.root.title(f"Busker {busker.__version__}")
    rv.root.columnconfigure(0, weight=1)
    rv.root.rowconfigure(0, weight=1)

    base = ttk.Frame(rv.root)
    base.columnconfigure(0, weight=1)
    base.rowconfigure(0, weight=1)
    base.rowconfigure(1, weight=0)

    base_split = ttk.PanedWindow(base, orient=tk.HORIZONTAL)
    base_split.grid(row=0, column=0, sticky="NESW")

    rv.tree_pnl = build_tree_panel(base_split)
    base_split.add(rv.tree_pnl.frame, weight=0)

    # root.configure(menu=menubar)
    # https://tkdocs.com/tutorial/menus.html
    rv.context_menus = build_context_menus(rv.tree_pnl.tree_wgt)
    rv.content = build_content(rv.tree_pnl.tree_wgt, path=args.playlist)

    book = ttk.Notebook(base_split)
    book.enable_traversal()
    base_split.add(book)

    rv.edit_pnl = build_edit_panel(base_split)
    book.add(rv.edit_pnl.split, text=rv.edit_pnl.name)
    rv.log_pnl = build_log_panel(base_split)
    book.add(rv.log_pnl.frame, text=rv.log_pnl.name)
    rv.status_pnl = build_status_panel(base)
    rv.status_pnl.frame.grid(row=1, column=0, sticky="NESW")

    rv.main_menu = build_main_menu(base, gui=rv)
    rv.root.configure(menu=rv.main_menu.menu)
    base.grid(row=0, column=0, sticky="NESW")
    rv.root.grid()

    rv.root.after(500, Clerk.monitor, rv)
    return rv


def start():
    pass


def main(args):
    args.playlist.mkdir(parents=True, exist_ok=True)
    gui = build_gui(args)
    print(f"{gui.theme.theme_names=}")
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
    logger = logging.getLogger("main")
    if args.playlist:
        if args.playlist.is_file():
            p.print_help()
            logger.error(f"'{args.playlist}' is a file. A playlist is a directory.")
            sys.exit(2)
        elif args.playlist.is_dir():
            p.print_help()
    rv = main(args)
    sys.exit(rv)


if __name__ == "__main__":
    run()
