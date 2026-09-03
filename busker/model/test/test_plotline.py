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
from collections import Counter
from collections import UserDict
from collections import UserList
from collections import UserString
import pathlib
import textwrap
import unittest

from busker.model.journal import Journal
from busker.model.multipart import Multipart
from busker.model.plotline import Plotline
from busker.model.types import Chain
from busker.model.types import Element
from busker.model.types import ElementType
from busker.model.types import Frame
from busker.model.types import Lens


class PlotlineTests(unittest.TestCase):

    texts = [
        textwrap.dedent("""
        {"seal": 2863490869328, "type": "application/json"}
        {
        "type": "context",
        "step": 2,
        "score": 0
        }
        {"seal": 2863490869328, "type": "text/x-python"}
        {
        "type": "context",
        "world": [
            {"inside": {"spot": 1}},
            {"outside": {"spot": 2}}
        ]
        }
        {"seal": 2863490869328, "type": "application/json"}
        {
            "type": "handler",
            "params": {
                "entity": "$[*]['description']"
            },
            "terms": [
                "Inspect {entity}"
            ]
        }
        {"seal": 2863490869328, "type": "application/x-python"}

        def fn(context: dict, **kwargs):
            context["score"] += 1

        {"seal": 2863490869328, "type": "application/json", "path": ["a"]}
        {
        "type": "context",
        "description": "outside"
        }
        {"seal": 2863490869328, "type": "application/json", "path": ["a"]}
        {
        "type": "marking",
        "name": "stage",
        "path": ["a", "b"],
        "face": [0, 1],
        "span": 12,
        "tick": 0
        }
        {"seal": 2863490869328, "type": "application/json", "path": ["a"]}
        {
        "type": "context",
        "rank": 1
        }
        {"seal": 2863490869328, "type": "application/json", "path": ["a", "b"]}
        {
        "type": "context",
        "description": "inside"
        }
        {"seal": 2863490869328, "type": "application/json", "path": ["a", "b"]}
        {
        "type": "content",
        "status": "draft"
        }
        {"seal": 2863490869328, "type": "text/plain", "path": ["a", "b"]}
        Yesterday, upon the stair

        {"seal": 2863490869328, "type": "text/plain", "path": ["a", "b"]}
        I met a man who wasn't there.

        {"seal": 2863490869328, "type": "text/plain", "path": ["a", "b"]}
        He wasn't there again today,

        {"seal": 2863490869328, "type": "text/plain", "path": ["a", "b"]}
        I wish that man would go away!

        """).lstrip(),
        textwrap.dedent("""
        {"seal": 127416676279376, "type": "application/json", "path": []}
        {
        "type": "marking",
        "path": ["spots", "bedroom"],
        "pose": 0
        }
        {"seal": 127416676279376, "type": "application/json", "path": ["spots", "bedroom"]}
        {
        "type": "linkage",
        "port": 20260813190453,
        "link": 20260813190710
        }
        {"seal": 127416676279376, "type": "application/json", "path": ["spots", "bedroom", "door"]}
        {
        "type": "linkage",
        "port": 20260813190710,
        "link": 20260813190453
        }
        {"seal": 127416676279376, "type": "application/json", "path": ["spots", "bedroom", "door"]}
        {
        "type": "linkage",
        "port": 20260813201044,
        "link": 20260813190851
        }
        {"seal": 127416676279376, "type": "application/json", "path": ["spots", "hall"]}
        {
        "type": "linkage",
        "port": 20260813190851,
        "link": 20260813201044
        }
        {"seal": 127416676279376, "type": "application/json", "path": ["spots", "hall"]}
        {
        "type": "linkage",
        "port": 20260813201319,
        "link": 20260813201422
        }
        {"seal": 127416676279376, "type": "application/json", "path": ["spots", "hall"]}
        {
        "type": "linkage",
        "port": 20260813202041,
        "link": 20260813192820
        }
        {"seal": 127416676279376, "type": "application/json", "path": ["spots", "kitchen", "door"]}
        {
        "type": "linkage",
        "port": 20260813201422,
        "link": 20260813201319,
        "spin": [5, 8],
        "cost": 0
        }
        {"seal": 127416676279376, "type": "application/json", "path": ["spots", "kitchen", "door"]}
        {
        "type": "linkage",
        "port": 20260813191208,
        "link": 20260813191107,
        "spin": [1, 8],
        "cost": Infinity
        }
        {"seal": 127416676279376, "type": "application/json", "path": ["spots", "kitchen"]}
        {
        "type": "linkage",
        "port": 20260813191107,
        "link": 20260813191208
        }
        {"seal": 127416676279376, "type": "application/json", "path": ["spots", "stairs"]}
        {
        "type": "linkage",
        "port": 20260813192820,
        "link": 20260813202041,
        "spin": [1, 2],
        "cost": 3
        }
        """).lstrip(),
        textwrap.dedent("""
        {"seal": 127416676279376, "type": "application/json", "path": []}
        {
        "type": "context"
        }
        {"seal": 127416676279376, "type": "text/x-python", "path": ["a"]}
        {
        "type": "context",
        "day": "Sunday",
        "chord": ("A", "D", "E"),
        "goods": {"eggs", "milk"},
        "route": ["home", "shop", "home"],
        }
        {"seal": 127416676279376, "type": "application/json", "path": ["a", 0]}
        {
        "type": "context"
        }
        {"seal": 127416676279376, "type": "application/json", "path": ["a", 0, 1]}
        {
        "type": "context",
        "day": "Monday"
        }
        {"seal": 127416676279376, "type": "text/x-python", "path": ["a", 0, 1, 2]}
        {
        "type": "context",
        "chord": ("C", "F", "G"),
        "goods": {"tea", "biscuits", "milk"},
        "route": ["work", "shop", "work", "home"],
        }
        {"seal": 127416676279376, "type": "application/json", "path": ["b"]}
        {
        "type": "context",
        "day": "Monday"
        }
        {"seal": 127416676279376, "type": "application/json", "path": ["b", 0]}
        {
        "type": "context",
        "day": "Tuesday"
        }
        {"seal": 127416676279376, "type": "text/x-python", "path": ["b", 1]}
        {
        "type": "context",
        "day": "Wednesday",
        "chord": ("C", "F", "G"),
        "goods": {"crumpets", "milk"},
        "route": ["work", "shop", "work", "home"],
        }
        """).lstrip(),
    ]

    @staticmethod
    def build_journal(text):
        adaptor = Multipart(factory={dict: UserDict, list: UserList, str: UserString})
        lens = Plotline(adaptor)
        journal = Journal(adaptor, lens, uri=pathlib.Path("test.rht"))
        list(adaptor.scan(text))
        journal.model
        return journal

    def test_model(self):
        journal = self.build_journal(self.texts[0])
        rht = journal.model
        for path, frame in rht.items():
            with self.subTest(frame=frame, path=path):
                self.assertIsInstance(frame, Frame)
                self.assertIsInstance(frame.path, tuple)
                self.assertEqual(frame.path, path)

                for elem in frame:
                    self.assertIsInstance(elem, (Element, ast.Module, UserString))
                    self.assertEqual(elem.parent, frame)

    def test_plotline_mesh(self):
        journal = self.build_journal(self.texts[1])
        plotline = journal.registry[Lens][0]
        rht = journal.model
        count = Counter(
           e.get(k) for p, f in rht.items() for e in f for k in ("port", "link")
           if e.get("type") == ElementType.LINKAGE.value
        )
        self.assertTrue(all(v == 2 for v in count.values()))
        mesh = list(plotline.mesh)
        self.assertEqual(len(count), len(mesh) + 1, mesh)  # Kitchen door is stuck

    def test_plotline_branches(self):
        journal = self.build_journal(self.texts[1])
        plotline = journal.registry[Lens][0]

        self.assertEqual(3, len(plotline.branches(("spots", "hall"))))

        branches = {i[0].port: i for i in plotline.branches(("spots", "hall"))}
        self.assertEqual(
            set(i[1].path for i in branches.values()),
            {("spots", "bedroom", "door"), ("spots", "kitchen", "door"), ("spots", "stairs")}
        )

        branches = {i[0].port: i for i in plotline.branches(("spots", "stairs"))}
        self.assertEqual(set(i[1].path for i in branches.values()), {("spots", "hall")})

    def test_plotline_route(self):
        journal = self.build_journal(self.texts[1])
        plotline = journal.registry[Lens][0]

        r = plotline.route(("spots", "kitchen"), ("spots", "bedroom"))
        self.assertEqual(5, len(r), r)
        self.assertEqual(5, len(set(r)))
        self.assertEqual(
            r,
            (("spots", "kitchen"), ("spots", "kitchen", "door"), ("spots", "hall"),
             ("spots", "bedroom", "door"), ("spots", "bedroom")),
            r
        )
