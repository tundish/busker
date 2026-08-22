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
import textwrap
import unittest

from busker.model.multipart import Multipart
from busker.model.plotline import Plotline
from busker.model.types import Chain
from busker.model.types import Element
from busker.model.types import Frame


class PlotlineTests(unittest.TestCase):

    texts = [
        textwrap.dedent("""
        {"mark": 2863490869328, "type": "application/json"}
        {
        "type": "context",
        "step": 2,
        "score": 0
        }
        {"mark": 2863490869328, "type": "text/x-python"}
        {
        "type": "context",
        "world": [
            {"inside": {"spot": 1}},
            {"outside": {"spot": 2}}
        ]
        }
        {"mark": 2863490869328, "type": "application/json"}
        {
            "type": "actions",
            "params": {
                "marker": "$['marker']",
                "place": "$[*]['description']"
            },
            "phrases": [
                "Go {place}"
            ]
        }
        {"mark": 2863490869328, "type": "text/x-python"}

        def fn(context: dict, place: str, marker: dict, **kwargs):
            context["score"] += 1

        {"mark": 2863490869328, "type": "application/json", "path": ["a"]}
        {
        "type": "context",
        "description": "outside"
        }
        {"mark": 2863490869328, "type": "application/json", "path": ["a"]}
        {
        "type": "marking",
        "rank": 0
        }
        {"mark": 2863490869328, "type": "application/json", "path": ["a"]}
        {
        "type": "context",
        "rank": 1
        }
        {"mark": 2863490869328, "type": "application/json", "path": ["a", "b"]}
        {
        "type": "context",
        "description": "inside"
        }
        {"mark": 2863490869328, "type": "application/json", "path": ["a", "b"]}
        {
        "type": "content",
        "status": "draft"
        }
        {"mark": 2863490869328, "type": "text/plain", "path": ["a", "b"]}
        Yesterday, upon the stair

        {"mark": 2863490869328, "type": "text/plain", "path": ["a", "b"]}
        I met a man who wasn't there.

        {"mark": 2863490869328, "type": "text/plain", "path": ["a", "b"]}
        He wasn't there again today,

        {"mark": 2863490869328, "type": "text/plain", "path": ["a", "b"]}
        I wish that man would go away!

        """).lstrip(),
        textwrap.dedent("""
        {"mark": 127416676279376, "type": "application/json", "path": []}
        {
        "type": "marking",
        "path": ["spots", "bedroom"],
        "pose": 0
        }
        {"mark": 127416676279376, "type": "application/json", "path": ["spots", "bedroom"]}
        {
        "type": "linkage",
        "port": 20260813190453,
        "link": 20260813190710
        }
        {"mark": 127416676279376, "type": "application/json", "path": ["spots", "bedroom", "door"]}
        {
        "type": "linkage",
        "port": 20260813190710,
        "link": 20260813190453
        }
        {"mark": 127416676279376, "type": "application/json", "path": ["spots", "bedroom", "door"]}
        {
        "type": "linkage",
        "port": 20260813201044,
        "link": 20260813190851
        }
        {"mark": 127416676279376, "type": "application/json", "path": ["spots", "hall"]}
        {
        "type": "linkage",
        "port": 20260813190851,
        "link": 20260813201044
        }
        {"mark": 127416676279376, "type": "application/json", "path": ["spots", "hall"]}
        {
        "type": "linkage",
        "port": 20260813201319,
        "link": 20260813201422
        }
        {"mark": 127416676279376, "type": "application/json", "path": ["spots", "hall"]}
        {
        "type": "linkage",
        "port": 20260813202041,
        "link": 20260813192820
        }
        {"mark": 127416676279376, "type": "application/json", "path": ["spots", "kitchen", "door"]}
        {
        "type": "linkage",
        "port": 20260813201422,
        "link": 20260813201319,
        "spin": [5, 8],
        "cost": 0,
        "open": true
        }
        {"mark": 127416676279376, "type": "application/json", "path": ["spots", "kitchen", "door"]}
        {
        "type": "linkage",
        "port": 20260813191208,
        "link": 20260813191107,
        "spin": [1, 8],
        "cost": 0,
        "open": true
        }
        {"mark": 127416676279376, "type": "application/json", "path": ["spots", "kitchen"]}
        {
        "type": "linkage",
        "port": 20260813191107,
        "link": 20260813191208
        }
        {"mark": 127416676279376, "type": "application/json", "path": ["spots", "stairs"]}
        {
        "type": "linkage",
        "port": 20260813192820,
        "link": 20260813202041,
        "spin": [1, 2],
        "cost": 3,
        "open": true
        }
        """).lstrip(),
        textwrap.dedent("""
        {"mark": 127416676279376, "type": "application/json", "path": []}
        {
        "type": "context"
        }
        {"mark": 127416676279376, "type": "text/x-python", "path": ["a"]}
        {
        "type": "context",
        "day": "Sunday",
        "chord": ("A", "D", "E"),
        "goods": {"eggs", "milk"},
        "route": ["home", "shop", "home"],
        }
        {"mark": 127416676279376, "type": "application/json", "path": ["a", 0]}
        {
        "type": "context"
        }
        {"mark": 127416676279376, "type": "application/json", "path": ["a", 0, 1]}
        {
        "type": "context",
        "day": "Monday"
        }
        {"mark": 127416676279376, "type": "text/x-python", "path": ["a", 0, 1, 2]}
        {
        "type": "context",
        "chord": ("C", "F", "G"),
        "goods": {"tea", "biscuits", "milk"},
        "route": ["work", "shop", "work", "home"],
        }
        {"mark": 127416676279376, "type": "application/json", "path": ["b"]}
        {
        "type": "context",
        "day": "Monday"
        }
        {"mark": 127416676279376, "type": "application/json", "path": ["b", 0]}
        {
        "type": "context",
        "day": "Tuesday"
        }
        {"mark": 127416676279376, "type": "text/x-python", "path": ["b", 1]}
        {
        "type": "context",
        "day": "Wednesday",
        "chord": ("C", "F", "G"),
        "goods": {"crumpets", "milk"},
        "route": ["work", "shop", "work", "home"],
        }
        """).lstrip(),
    ]

    def test_scan(self):
        rht = Plotline.scan(self.texts[0])
        for path, frame in rht.doc.data.items():
            with self.subTest(frame=frame, path=path):
                self.assertIsInstance(frame, Frame)
                self.assertIsInstance(frame.path, tuple)
                self.assertEqual(frame.path, path)

                for elem in frame:
                    self.assertIsInstance(elem, (Element, ast.Module, UserString))
                    self.assertEqual(elem.parent, frame)

    def test_scan_context(self):
        rht = Plotline.scan(self.texts[0])
        self.assertIsInstance(rht.doc.data[()][0], Element)
        self.assertEqual(rht.doc.data[()][0].get("type"), rht.Type.CONTEXT.value)

        self.assertIsInstance(rht.doc.data[()][1], Element)
        self.assertEqual(rht.doc.data[()][1].get("type"), rht.Type.CONTEXT.value)

    def test_plotline_mesh(self):
        rht = Plotline.scan(self.texts[1])
        count = Counter(
           e.get(k) for p, f in rht.doc.data.items() for e in f for k in ("port", "link")
           if e.get("type") == rht.Type.LINKAGE.value
        )
        self.assertTrue(all(v == 2 for v in count.values()))
        mesh = list(rht.mesh)
        self.assertEqual(len(count), len(mesh), mesh)

    def test_plotline_branches(self):
        rht = Plotline.scan(self.texts[1])

        self.assertEqual(3, len(rht.branches(("spots", "hall"))))

        branches = {i[0].port: i for i in rht.branches(("spots", "hall"))}
        self.assertEqual(
            set(i[1].path for i in branches.values()),
            {("spots", "bedroom", "door"), ("spots", "kitchen", "door"), ("spots", "stairs")}
        )

        branches = {i[0].port: i for i in rht.branches(("spots", "stairs"))}
        self.assertEqual(set(i[1].path for i in branches.values()), {("spots", "hall")})

    def test_plotline_route(self):
        rht = Plotline.scan(self.texts[1])
        r = rht.route(("spots", "kitchen"), ("spots", "bedroom"))
        self.assertEqual(5, len(r), r)
        self.assertEqual(5, len(set(r)))
        self.assertEqual(
            r,
            (("spots", "kitchen"), ("spots", "kitchen", "door"), ("spots", "hall"),
             ("spots", "bedroom", "door"), ("spots", "bedroom")),
            r
        )

    def test_plotline_context(self):
        rht = Plotline.scan(self.texts[2])

        path = ("a", 0, 1, 2)
        with self.subTest(path=path):
            rv = rht.context(path)
            self.assertIsInstance(rv, Chain)
            self.assertTrue(isinstance(i, Element) for i in rv.maps)
            self.assertEqual(rv["type"], rht.Type.CONTEXT.value)
            self.assertEqual(rv["chord"], ("C", "F", "G"), rht.doc.data)
            self.assertEqual(rv["goods"], {"tea", "biscuits", "eggs", "milk"})
            self.assertEqual(rv["route"], ["home", "shop", "home", "work", "shop", "work", "home"], rv)

    def test_plotline_journal(self):
        rht = Plotline.scan(self.texts[2])
        rv = rht.journal
        self.assertIsInstance(rv, dict)
        self.assertEqual(("a", "b"), tuple(rv))
