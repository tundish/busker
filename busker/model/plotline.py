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
from collections import ChainMap
from collections import defaultdict
from collections import namedtuple
from collections import UserDict
from collections import UserList
from collections import UserString
from collections.abc import Generator

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
    """
    Implements a Resource HyperTree (.rht).

    """

    class Type(enum.StrEnum):
        ACTIONS = enum.auto()
        CONTENT = enum.auto()
        CONTEXT = enum.auto()
        LINKAGE = enum.auto()
        MARKING = enum.auto()

    Point = namedtuple(
        "Point", ["path", "port", "spin", "cost"], defaults=[0, 0]
    )

    @classmethod
    def scan(cls, text: str):
        """
        Read through the text and assemble a Multipart document.
        Decorate each frame with its path, and each Element with its type.

        """
        doc = Multipart(text=text, factory={dict: UserDict, list: UserList, str: UserString})
        for p in list(doc.data):
            frame = doc.data[p] = Frame(doc.data[p].data)
            frame.path = p
            for n, obj in enumerate(frame.copy()):
                try:
                    typ = cls.Type[obj["type"].upper()]
                    frame[n] = Element(obj.data)
                    frame[n].type = typ
                except (AttributeError, TypeError):
                    pass
                finally:
                    frame[n].parent = frame
            frame.refresh()
        return cls(doc)

    def __init__(self, doc: Multipart):
        self.doc = doc
        self.routes = {}

    @property
    def mesh(self) -> Generator:
        """
        Generate the topological mesh of linked paths

        Each item is a tuple representing an arc from one path to another, if ports are open.
        Turn value, when known, is the second element of the tuple.

        """
        linkage_elements = {
            elem.get("port"): elem
            for frame in self.doc.data.values()
            for elem in frame
            if elem.type == self.Type.LINKAGE
        }

        for port, elem in linkage_elements.items():
            twin = linkage_elements[elem["link"]]
            if not elem.get("open", True):
                continue

            yield (
                self.Point(
                    elem.parent.path, elem["port"],
                    tuple(elem.get("spin", [0, 1])), elem.get("cost", 0)
                ),
                self.Point(
                    twin.parent.path, twin["port"],
                    tuple(twin.get("spin", [0, 1])), twin.get("cost", 0)
                ),
            )

    def branches(self, path: tuple) -> set[tuple, tuple]:
        """
        Returns a set of the permitted exits from the supplied path.

        """
        return {(a, b) for a, b in self.mesh if a.path == path}

    def route(self, start: tuple, end: tuple) -> list[tuple]:
        """
        Return a list containing the shortest route between the spots `start` and `end`.
        The endpoints are included in the output.

        """
        if (start, end) in self.routes:
            return self.routes[(start, end)][0]

        proven = set()
        incomplete = [[start]]

        topology = defaultdict(set)
        for a, b in self.mesh:
            topology[a.path].add(b.path)

        n = len(topology)
        d = 1
        while n >= 0 or not proven:
            options = []
            for candidate in incomplete:
                if candidate[-1] == end:
                    proven.add(tuple(candidate))
                else:
                    hops = topology[candidate[-1]]
                    d = len(hops)
                    for hop in hops:
                        if hop not in candidate:
                            options.append(candidate.copy())
                            options[-1].append(hop)
            incomplete = options
            n = n - d

        rv = self.routes[(start, end)] = sorted(proven, key=len) if proven else []
        return rv[0]
