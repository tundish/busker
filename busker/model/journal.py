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
from busker.model.plotline import Plotline
from busker.model.types import Chain
from busker.model.types import Element
from busker.model.types import Frame


class Journal(Plotline):
    """
    Access to Resource HyperTree (.rht) data.

    """

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

    @property
    def journal(self) -> dict:
        "Expand the document into a nested tree of frames"
        rv = dict()
        done = dict()
        paths = list(self.doc.data)
        for path in paths:
            node = rv
            for n, key in enumerate(path):
                pos = tuple(path[:n + 1])
                if pos in done:
                    node = done[pos]
                    continue

                try:
                    frame = self.doc.data[pos]
                    node[key] = Chain(*(i for i in frame if i.type == self.Type.CONTEXT.value))
                except KeyError:
                    node[key] = Chain()

                node[key] = node[key].new_child()
                done[pos] = node[key]
        return rv

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
