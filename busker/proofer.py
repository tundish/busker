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
#! /usr/bin/env python
# encoding: utf-8

from collections import namedtuple
import pathlib
import string

from busker.stager import Stager
from busker.utils.graph import load_rules


class Proofer:

    Script = namedtuple("Script", ["path", "text", "tables"], defaults=["", dict()])

    def __init__(self, stager: Stager = None):
        self.stager = stager
        self.formatter = string.Formatter()

    def read_scenes(self, paths: list[pathlib.Path]):
        for path in paths:
            try:
                text = path.read_text()
            except FileNotFoundError:
                continue
            else:
                yield
