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
import unittest

from busker.model.journal import Journal
from busker.model.plotline import Plotline
from busker.model.types import Chain
from busker.model.types import Element
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
        self.assertEqual(rht.doc.data[()][0].get("type"), rht.Type.CONTEXT.value)

        self.assertIsInstance(rht.doc.data[()][1], Element)
        self.assertEqual(rht.doc.data[()][1].get("type"), rht.Type.CONTEXT.value)

    def test_journal_context(self):
        rht = Journal.scan(PlotlineTests.texts[2])

        path = ("a", 0, 1, 2)
        for n in range(3):
            with self.subTest(path=path, n=n):
                rv = rht.context(path)
                self.assertIsInstance(rv, Chain)
                self.assertTrue(isinstance(i, Element) for i in rv.maps)
                self.assertEqual(rv["type"], rht.Type.CONTEXT.value)
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

    def test_search_context(self):
        rht = Journal.scan(PlotlineTests.texts[2])
        context = rht.context(("b", 1))
        print(context)
        self.assertIsInstance(context.maps[0].parent, Frame)
        self.assertEqual(context.maps[0].type.value, rht.Type.CONTEXT.value)

        rv = rht.search("$['day']", context)
        self.assertIsInstance(rv, list)

