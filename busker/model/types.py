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

import ast
from collections import ChainMap
from collections import UserDict
from collections import UserList
from collections import UserString
import enum


class ElementType(enum.StrEnum):
    CONTENT = enum.auto()
    CONTEXT = enum.auto()
    FIXTURE = enum.auto()
    HANDLER = enum.auto()
    LINKAGE = enum.auto()
    MARKING = enum.auto()
    MONITOR = enum.auto()
    TRIGGER = enum.auto()


class Chain(ChainMap):
    "Variant of ChainMap that allows direct updates to inner scopes"

    def __setitem__(self, key, value):
        for mapping in self.maps:
            if key in mapping:
                mapping[key] = value
                return
        self.maps[0][key] = value

    def __delitem__(self, key):
        for mapping in self.maps:
            if key in mapping:
                del mapping[key]
                return
        raise KeyError(key)


class Frame(UserList):
    def refresh(self):
        for obj in self.data:
            try:
                obj.refresh(parent=self)
            except AttributeError:
                pass
        return self


class Element(UserDict):

    @property
    def handler(self):
        if self.data.get("type") != ElementType.HANDLER.value:
            return

        try:
            pos = self.parent.index(self)
        except ValueError:
            return

        try:
            rv = self.parent[pos + 1]
        except IndexError:
            return

        if isinstance(rv, ast.AST):
            return rv

    def refresh(self, parent=None):
        self.parent = parent
        return self
