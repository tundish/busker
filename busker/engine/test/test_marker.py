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

from collections import UserDict
from collections import UserList
from collections import UserString
import importlib.resources
import textwrap
import unittest

from busker.engine.marker import Marker
from busker.model.journal import Journal
from busker.model.multipart import Multipart
from busker.model.types import Frame


class MarkerTests(unittest.TestCase):

    def setUp(self):
        self.text = textwrap.dedent("""
        {"seal": 2863490869328, "type": "application/json", "path": ["a"]}
        {
        "type": "marking",
        "name": "world_focus",
        "view": ["a", "b"],
        "face": [0, 1],
        "span": 12,
        "tick": 0,
        "memo": {
            "['b', 'c']": 3
        }
        }
        """).lstrip()

    def test_marker_via_dict(self):
        params = {}
        rv = Marker(**params)
        self.assertIsInstance(rv, Marker)

    def test_marker_via_text(self):
        adaptor = Multipart(
            factory={
                dict: UserDict, list: UserList, str: UserString, "marking": Marker
            }
        )
        item = next(adaptor.scan(self.text), None)
        self.assertEqual(item.get("payload", {}).get("view"), ["a", "b"])
        self.assertEqual(list(adaptor.data), [(), ("a",)])

        element = adaptor.data[("a",)]
        self.assertIsInstance(getattr(element, "parent"), Frame)
        self.assertTrue(element)
        self.assertIsInstance(element, Marker)

    def test_marker_via_journal(self):
        adaptor = Multipart(
            factory={
                dict: UserDict, list: UserList, str: UserString, "marking": Marker
            }
        )
        items = list(adaptor.scan(self.text))
        journal = Journal(adaptor, uri="test.rht")

        frame = journal.model[("a",)]
        self.assertTrue(frame)
        self.assertIsInstance(frame, Frame)

        element = frame[0]
        self.assertIs(getattr(element, "parent"), frame)
        self.assertIsInstance(element, Marker)
