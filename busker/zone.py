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

from collections import defaultdict
import pathlib
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace as Structure

from busker.history import SharedHistory


class Zone(SharedHistory):

    registry = defaultdict(list)

    def __init__(self, parent, name="", **kwargs):
        super().__init__(log_name=f"busker.gui.{name.lower()}", **kwargs)
        self.registry[self.__class__.__name__].append(self)

        self.parent = parent
        self.name = name
        self.frame = ttk.LabelFrame(parent, text=name)

        container = defaultdict(list)
        for attr, obj in self.build(self.frame):
            container[attr].append(obj)
        self.controls = Structure(**container)

    @staticmethod
    def walk_files(path: pathlib.Path, callback=None):
        callback = callback or pathlib.Path
        if path.is_dir():
            for p in path.iterdir():
                yield from Zone.walk_files(pathlib.Path(p))
        yield callback(path)

    @staticmethod
    def grid(arg, **kwargs):
        arg.grid(**kwargs)
        return arg

    @staticmethod
    def build(frame: ttk.Frame):
        return
        yield
