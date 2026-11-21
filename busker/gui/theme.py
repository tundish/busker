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

from collections import namedtuple
import datetime
from functools import partial
import logging

import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

from types import SimpleNamespace as SN
import queue


class Theme:
    """
    Provides validation and logical consistency.
    Only loosely bound to a GUI.

    see bootstack/widgets/theme_toggle
    # TODO: apply fnmatch selection of elements

    """

    Params = namedtuple("ThemeParams", ["mode"])

    def __init__(self, root):
        self.root = root

    @property
    def theme_names(self):
        style = ttk.Style()
        print(f"{style.element_names()=}")
        return style.theme_names()

