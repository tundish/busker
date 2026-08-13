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


# TODO: Paths identify nodes (stage) or edges (story) depending on content.
# Both nodes and edges have ports which connect them.

# Stage: Python code (world entity query model)
# Story: Speech      (scene drama directives model)

# Marking: The current active location(s) in the Multipart.
# Context: A ChainMap of UserDict along the reverse path to the root.
# Linkage: Associations between separate locations in the Multipart.
# Actions: Declarations of commands which modify context and expedite marking.
# Content: Dialogue, Effects and Multimedia driven from Speech cues.

import enum
from collections import ChainMap
from collections import UserDict
from collections import UserList
from collections import UserString

from busker.model.multipart import Multipart


class Frame(UserList):
    def refresh(self):
        for obj in self.data:
            try:
                obj.refresh(parent=self)
            except AttributeError:
                pass
        return self


class Element(UserDict):
    def refresh(self, parent=None):
        self.parent = parent
        return self


class Plotline:

    class Type(enum.StrEnum):
        ACTIONS = enum.auto()
        CONTENT = enum.auto()
        CONTEXT = enum.auto()
        LINKAGE = enum.auto()
        MARKING = enum.auto()

    @classmethod
    def scan(cls, text: str):
        doc = Multipart(text=text, factory={dict: UserDict, list: UserList, str: UserString})
        for p in list(doc.data):
            frame = doc.data[p] = Frame(doc.data[p].data)
            for n, obj in enumerate(frame.copy()):
                try:
                    typ = cls.Type[obj["type"].upper()]
                    frame[n] = Element(obj.data)
                except (AttributeError, TypeError):
                    pass
            frame.refresh()
        return cls(doc)

    def __init__(self, doc: Multipart):
        self.doc = doc
