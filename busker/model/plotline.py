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
from collections import defaultdict
from collections import namedtuple
from collections import UserDict
from collections import UserList
from collections import UserString
from collections.abc import Generator
from collections.abc import Mapping
from collections.abc import MutableSequence
from collections.abc import Set
import itertools
import operator

from busker.model.multipart import Multipart
from busker.model.types import Chain
from busker.model.types import Element
from busker.model.types import Frame


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

    @staticmethod
    def merge(body: dict, item: dict):
        """
        Merge a new item (by copy) into the context body.
        Chains are built from the leaf up toward the root.
        Consequently ordered sequences are built first in, last out.

        """
        stack = [(body.copy(), item.copy())]
        while stack:
            body, item = stack.pop(0)
            for k, v in item.items():
                if isinstance(v, Set):
                    try:
                        body[k] = body[k].union(v)
                    except AttributeError:
                        v = list(v)
                    except KeyError:
                        body[k] = v
                        continue

                if isinstance(v, MutableSequence):
                    try:
                        # FILO
                        body[k] = v.copy() + body[k]
                    except AttributeError:
                        v = tuple(v)
                    except KeyError:
                        body[k] = v
                        continue

                if k not in body:
                    body[k] = v
                elif isinstance(body[k], Mapping):
                    stack.append((body[k].copy(), v))
        return body

    def __init__(self, doc: Multipart):
        self.doc = doc
        self.routes = {}

    @property
    def mesh(self) -> Generator[tuple]:
        """
        Generate the topological mesh of linked paths.

        Each item is a tuple representing an arc from one path to another, if ports are open.
        Spin and Cost values are given defaults if not defined.

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

    @property
    def journal(self) -> dict:
        rv = dict()
        paths = list(self.doc.data)
        for path in paths:
            node = rv
            for n, key in enumerate(path):
                pos = path[:n + 1]
                if pos in self.doc.data:
                    frame = self.doc.data[pos]
                    node[key] = Chain(*(i for i in frame if i.type == self.Type.CONTEXT.value))
                else:
                    node[key] = Chain()

                if pos != path:
                    node = node[key].new_child()
                print(f"{key=} {pos=} {node=}")
        return rv

    def branches(self, path: tuple) -> set[tuple, tuple]:
        """
        Returns a set of the permitted exits from the supplied path.

        """
        return {(a, b) for a, b in self.mesh if a.path == path}

    def context(self, path: tuple) -> Chain:
        levels = [path[0: n] for n in range(len(path) + 1)]
        frames = [self.doc.data.get(level, []) for level in levels]
        chains = [
            Chain(*(i for i in frame if i.type == self.Type.CONTEXT.value))
            for frame in reversed(frames)
        ]
        rv = list(itertools.accumulate(chains, self.merge))
        return rv[-1] if rv else {}

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
