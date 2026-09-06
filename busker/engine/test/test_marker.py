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
from busker.model.types import ElementType
from busker.model.types import Frame


class MarkerTests(unittest.TestCase):

    def setUp(self):
        self.text = textwrap.dedent("""
        {"seal": 20260906200320, "type": "application/json", "path": []}
        {
        "type": "marking",
        "name": "world_focus",
        "view": [0, 0],
        "face": [0, 1],
        "span": 12,
        "tick": 0,
        "memo": {
            "['b', 'c']": 3
        }
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 0]}
        # Centre square, N
        {
        "type": "linkage",
        "port": (0,0,0),
        "link": (0,1,4)
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 0]}
        # Centre square, NE
        {
        "type": "linkage",
        "port": (0,0,1),
        "link": (1,1,5),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 0]}
        # Centre square, E
        {
        "type": "linkage",
        "port": (0,0,2),
        "link": (1,0,6),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 0]}
        # Centre square, SE
        {
        "type": "linkage",
        "port": (0,0,3),
        "link": (1,1,7),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 0]}
        # Centre square, S
        {
        "type": "linkage",
        "port": (0,0,4),
        "link": (0,-1,0),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 0]}
        # Centre square, SW
        {
        "type": "linkage",
        "port": (0,0,5),
        "link": (-1,-1,1),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 0]}
        # Centre square, W
        {
        "type": "linkage",
        "port": (0,0,6),
        "link": (-1,0,2),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 0]}
        # Centre square, NW
        {
        "type": "linkage",
        "port": (0,0,7),
        "link": (-1,1,3),
        }
        """).lstrip()

    def test_marker_via_dict(self):
        params = dict(name="test_marker")
        rv = Marker(**params)
        self.assertIsInstance(rv, Marker)
        self.assertEqual(rv.view, ())
        self.assertEqual(rv.type, ElementType.MARKING.value)

    def test_marker_via_text(self):
        adaptor = Multipart(
            factory={
                dict: UserDict, list: UserList, str: UserString, "marking": Marker
            }
        )
        item = next(adaptor.scan(self.text), None)
        self.assertIsInstance(item.get("payload"), Marker)
        self.assertEqual(item["payload"].view, (0, 0))
        self.assertEqual(list(adaptor.data), [()])

        frame = adaptor.data[()]
        self.assertTrue(frame)
        self.assertIsInstance(frame[0], Marker)

    def test_marker_via_journal(self):
        adaptor = Multipart(
            factory={
                dict: UserDict, list: UserList, str: UserString, "marking": Marker
            }
        )
        items = list(adaptor.scan(self.text))
        journal = Journal(adaptor, uri="test.rht")

        frame = journal.model[()]
        self.assertTrue(frame)
        self.assertIsInstance(frame, Frame)
        self.assertEqual(getattr(frame, "path"), ())

        element = frame[0]
        self.assertIs(getattr(element, "parent"), frame)
        self.assertIsInstance(element, Marker)
