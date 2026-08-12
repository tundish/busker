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
from collections import UserDict
from collections import UserList
from collections import UserString

from busker.model.multipart import Multipart


class Plotline:

    class Type(enum.StrEnum):
        ACTIONS = enum.auto()
        CONTENT = enum.auto()
        CONTEXT = enum.auto()
        LINKAGE = enum.auto()
        MARKING = enum.auto()

    @classmethod
    def scan(text: str):
        return cls()

    def __init__(self, doc: Multipart):
        self.doc = doc
