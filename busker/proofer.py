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
import tomllib

from busker.stager import Stager
from busker.utils.graph import load_rules


class Proofer:

    Script = namedtuple("Script", ["path", "text", "tables", "errors"], defaults=["", dict(), list()])

    @classmethod
    def read_scenes(cls, paths: list[pathlib.Path], **kwargs):
        for path in paths:
            try:
                text = path.read_text()
            except FileNotFoundError:
                continue

            try:
                tables = tomllib.loads(text, **kwargs)
                errors = {}
            except tomllib.TOMLDecodeError as e:
                tables = {}
                line = int(next((i for i in str(e).split() if i.isdigit()), "1"))
                errors = {line: e}
            yield cls.Script(path, text, tables, errors)

    def __init__(self, stager: Stager = None):
        self.stager = stager
        self.formatter = string.Formatter()
