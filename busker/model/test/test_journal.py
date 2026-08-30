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
from collections import UserString
import logging
import platform
import textwrap
import unittest

from busker.model.journal import Journal
from busker.model.plotline import Plotline
from busker.model.types import Chain
from busker.model.types import Element
from busker.model.types import ElementType
from busker.model.types import Frame

from busker.model.test.test_plotline import PlotlineTests


class JournalTests(unittest.TestCase):

    def test_scan(self):
        rht = Journal.scan(PlotlineTests.texts[0])
        for path, frame in rht.doc.data.items():
            with self.subTest(frame=frame, path=path):
                self.assertIsInstance(frame, Frame)
                self.assertIsInstance(frame.path, tuple)
                self.assertEqual(frame.path, path)

                for elem in frame:
                    self.assertIsInstance(elem, (Element, ast.Module, UserString))
                    self.assertEqual(elem.parent, frame)

    def test_scan_context(self):
        rht = Journal.scan(PlotlineTests.texts[0])
        self.assertIsInstance(rht.doc.data[()][0], Element)
        self.assertEqual(rht.doc.data[()][0].get("type"), ElementType.CONTEXT.value)

        self.assertIsInstance(rht.doc.data[()][1], Element)
        self.assertEqual(rht.doc.data[()][1].get("type"), ElementType.CONTEXT.value)

    def test_journal_context(self):
        rht = Journal.scan(PlotlineTests.texts[2])

        path = ("a", 0, 1, 2)
        for n in range(3):
            with self.subTest(path=path, n=n):
                rv = rht.context(path)
                self.assertIsInstance(rv, Chain)
                self.assertTrue(isinstance(i, Element) for i in rv.maps)
                self.assertEqual(rv["type"], ElementType.CONTEXT.value)
                self.assertEqual(rv["chord"], ("C", "F", "G"), rht.doc.data)
                self.assertEqual(rv["goods"], {"tea", "biscuits", "eggs", "milk"})
                self.assertEqual(rv["route"], ["home", "shop", "home", "work", "shop", "work", "home"], rv)

    def test_journal(self):
        rht = Journal.scan(PlotlineTests.texts[2])
        rv = rht.tree
        self.assertIsInstance(rv, dict)
        self.assertEqual(("a", "b"), tuple(rv), rv)
        self.assertIn(0, rv["a"], rv)
        self.assertIn(1, rv["a"][0])
        self.assertIn(2, rv["a"][0][1])
        self.assertEqual(rv["a"][0][1][2]["goods"], {"tea", "biscuits", "milk"})
        self.assertIs(rv["a"][0][1][2].maps[1], rht.doc.data[("a", 0, 1, 2)][0])

    def test_search_context_key(self):
        rht = Journal.scan(PlotlineTests.texts[2])
        context = rht.context(("b", 1))
        self.assertIsInstance(context.maps[0].parent, Frame)

        rv = rht.search("$['day']", context)
        self.assertEqual(rv, ["Wednesday"])

    def test_search_context_attribute(self):
        rht = Journal.scan(PlotlineTests.texts[2])
        context = rht.context(("b", 1))
        self.assertEqual(context.maps[0].type.value, ElementType.CONTEXT.value)

        rv = rht.search("$.maps[0].type.value", context)
        self.assertEqual(rv, ["context"])

    @unittest.skipIf(platform.python_version() < "3.13", "new eval semantics")
    def test_compile_exec_action(self):
        action_text = textwrap.dedent("""
        {"seal": 127416676279376, "type": "application/json", "path": []}
        {
        "type": "handler",
        "description": "Carry shopping",
        "params": {
            "goods": "$['goods'][*]",
            "place": "$['route'][*]"
        },
        "terms": [
            "Carry {goods} {place}",
            "Drop off {goods} at {place}"
        ]
        }
        {"seal": 127416676279376, "type": "application/x-python"}
        context = journal.context(path)
        context["goods"].remove(goods)
        logging.getLogger(format(path)).debug(
            f"Removed goods '{goods}' from context '{path}'"
        )
        """)
        text = PlotlineTests.texts[2] + action_text
        rht = Journal.scan(text)
        path = ("b", 1)
        actions = rht.actions(path)
        self.assertIsInstance(actions, dict)
        rv = actions.get("Drop off milk at work")
        self.assertIsInstance(rv, tuple)
        self.assertEqual(len(rv), 2)
        self.assertIsInstance(rv[0], Element)
        self.assertEqual(rv[0], rht.doc.data[()][-2])
        self.assertEqual(rv[0].handler, rht.doc.data[()][-1])
        self.assertEqual(rv[1], dict(goods="milk", place="work"))

        self.assertEqual(rht.context(path).get("goods", None), {"crumpets", "milk"})
        code = compile(rv[0].handler, format(path), mode="exec")
        l = dict(rv[1], journal=rht, path=path)
        g = dict(logging=logging)
        with self.assertLogs(format(path), logging.DEBUG) as check:
            exec(code, locals=l, globals=g)

        self.assertTrue(check.output)
        self.assertIn("Removed goods 'milk' from context", check.output[0])
        self.assertEqual(rht.context(path).get("goods", None), {"crumpets"})
