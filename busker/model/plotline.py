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
from collections.abc import Generator
from collections import ChainMap
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

    @property
    def topology(self) -> Generator:
        """
        Generates the topological mesh of the map.

        Each item is a tuple representing an arc from one spot to another, if permitted by a transit.
        Compass direction, when known, is the second element of the tuple.

        The built map of the previous example generates the following six arcs:

        .. code-block:: python
           :linenos:

           (<Exit.bedroom: ['bedroom']>, None, Transit(names=['bedroom door'], ...), <Into.hall: ['hall', 'hallway']>)
           (<Into.hall: ['hall', 'hallway']>, None, Transit(names=['bedroom door'], ...), <Exit.bedroom: ['bedroom']>)
           (<Exit.hall: ['hall', 'hallway']>, <Compass.N: ['North', (0, 1, 0)]>, Transit(names=[], ...), <Into.stairs: ['stairs', ...]>)
           (<Into.stairs: ['stairs', ...]>, <Compass.S: ['South', (0, -1, 0)]>, Transit(names=[], ...) <Exit.hall: ['hall', 'hallway']>)
           (<Exit.kitchen: ['kitchen']>, <Compass.SW: ['Southwest', 'South West', (-1, -1, 0)]>, Transit(names=['kitchen door'], ...) <Into.hall: ['hall', 'hallway']>)
           (<Into.hall: ['hall', 'hallway']>, <Compass.NE: ['Northeast', 'North East', (1, 1, 0)]>, Transit(names=['kitchen door'], ...) <Exit.kitchen: ['kitchen']>)

        """
        for t in self.transits:
            d = t.get_state(self.exit)
            a = t.get_state(self.into)
            v = t.get_state(Traffic)
            c = t.get_state(Compass)
            b = c and c.back
            if v in (Traffic.flowing, Traffic.forward):
                yield d, c, t, a
            if v in (Traffic.flowing, Traffic.reverse):
                yield a, b, t, d

    def options(self, spot: dict) -> set:
        """
        Returns a set of all the permitted transits from the supplied spot.
        Each item of the set is a tuple of three elements.
        The first is a compass heading if one is defined, otherwise it's an integer unique in the result set. 
        The second element is the destination spot. The third is the viable transit.

        Using the example above, this line of code will return a set with three items:

        >>> map.options(map.spot.hall)
        {(<Compass.NE: ['Northeast', 'North East', (1, 1, 0)]>, <Spot.kitchen: ['kitchen']>, Transit(names=['kitchen door'], ...),
        (<Compass.N: ['North', (0, 1, 0)]>, <Spot.stairs: ['stairs', ...]>, Transit(names=[], ...)),
        (1, <Spot.bedroom: ['bedroom']>, Transit(names=['bedroom door'], ...))}

        """
        typ = type(spot)
        return {
            (c or n, typ[a.name], t)
            for n, (d, c, t, a) in enumerate(self.topology)
            if d.name == spot.name
        }

    def route(self, start: tuple, end: tuple) -> list[tuple]:
        """
        Return a list containing the shortest route between the spots `start` and `end`.
        The endpoints are included in the output.

        >>> map.route(map.spot.kitchen, map.spot.bedroom)
        [<Spot.kitchen: ['kitchen']>,
         <Spot.hall: ['hall', 'hallway']>,
         <Spot.bedroom: ['bedroom']>]
        """
        if (start.name, end.name) in self.routes:
            return self.routes[(start.name, end.name)]

        rvs = set()
        paths = [[start.name]]

        graph = defaultdict(set)
        for d, _, t, a in self.topology:
            graph[d.name].add(a.name)

        n = len(graph)
        d = 1
        while n >= 0 or not rvs:
            nxt = []
            for p in paths:
                if p[-1] == end.name:
                    rvs.add(tuple(p))
                else:
                    nodes = graph[p[-1]]
                    d = len(nodes)
                    for i in nodes:
                        if i not in p:
                            nxt.append(p.copy())
                            nxt[-1].append(i)
            paths = nxt
            n = n - d

        rv = [type(start)[i] for i in sorted(rvs, key=len)[0]] if rvs else []
        self.routes[(start.name, end.name)] = rv
        return rv

    def __init__(self, doc: Multipart):
        self.doc = doc
