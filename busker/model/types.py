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

from collections import ChainMap
from collections import UserDict
from collections import UserList
from collections import UserString
import enum


class ElementType(enum.StrEnum):
    ACTIONS = enum.auto()
    CONTENT = enum.auto()
    CONTEXT = enum.auto()
    LINKAGE = enum.auto()
    MARKING = enum.auto()


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
    def action(self):
        if self.data.get("type") != ElementType.ACTIONS.value:
            return

    def refresh(self, parent=None):
        self.parent = parent
        return self
