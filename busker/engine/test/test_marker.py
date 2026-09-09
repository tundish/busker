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

from collections import Counter
from collections import UserDict
from collections import UserList
from collections import UserString
import importlib.resources
import textwrap
import unittest

from busker.engine.marker import Marker
from busker.model.journal import Journal
from busker.model.multipart import Multipart
from busker.model.travel import Travel
from busker.model.types import ElementType
from busker.model.types import Frame


class MarkerTests(unittest.TestCase):

    def setUp(self):
        self.text = textwrap.dedent("""
        {"seal": 20260906200320, "type": "data/python", "path": []}
        {
        "type": "marking",
        "name": "world_focus",
        "view": [0, 0],
        "face": (0, 1),
        "span": 1,
        "tick": 0,
        "twist": False,
        "memo": {
            (0, 0): 3,
        }
        }
        {"seal": 20260906200320, "type": "text/plain", "path": []}
        This test data is a grid of nine squares. The square in the centre
        is connected to its neighbours in 8 directions. The outer squares
        return these links back to the centre and communicate in N,E,S,W
        directions with each other.
        {"seal": 20260906200320, "type": "data/python", "path": [0, 0]}
        # Centre square, N
        {
        "type": "linkage",
        "port": (0,0,0),
        "link": (0,1,4),
        "spin": (0, 1),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 0]}
        # Centre square, NE
        {
        "type": "linkage",
        "port": (0,0,1),
        "link": (1,1,5),
        "spin": (1, 8),
        "cost": 2,
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 0]}
        # Centre square, E
        {
        "type": "linkage",
        "port": (0,0,2),
        "link": (1,0,6),
        "spin": (1, 4),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 0]}
        # Centre square, SE
        {
        "type": "linkage",
        "port": (0,0,3),
        "link": (1,-1,7),
        "spin": (3, 8),
        "cost": 2,
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 0]}
        # Centre square, S
        {
        "type": "linkage",
        "port": (0,0,4),
        "link": (0,-1,0),
        "spin": (1, 2),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 0]}
        # Centre square, SW
        {
        "type": "linkage",
        "port": (0,0,5),
        "link": (-1,-1,1),
        "spin": (5, 8),
        "cost": 2,
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 0]}
        # Centre square, W
        {
        "type": "linkage",
        "port": (0,0,6),
        "link": (-1,0,2),
        "spin": (3, 4),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 0]}
        # Centre square, NW
        {
        "type": "linkage",
        "port": (0,0,7),
        "link": (-1,1,3),
        "spin": (7, 8),
        "cost": 2,
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 1]}
        # North square, E
        {
        "type": "linkage",
        "port": (0,1,2),
        "link": (1,1,6),
        "spin": (1, 4),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 1]}
        # North square, S
        {
        "type": "linkage",
        "port": (0,1,4),
        "link": (0,0,0),
        "spin": (1, 2),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, 1]}
        # North square, W
        {
        "type": "linkage",
        "port": (0,1,6),
        "link": (-1,1,2),
        "spin": (3, 4),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [1, 1]}
        # NorthEast square, S
        {
        "type": "linkage",
        "port": (1,1,4),
        "link": (1,0,0),
        "spin": (1, 2),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [1, 1]}
        # NorthEast square, SW
        {
        "type": "linkage",
        "port": (1,1,5),
        "link": (0,0,1),
        "spin": (5, 8),
        "cost": 2,
        }
        {"seal": 20260906200320, "type": "data/python", "path": [1, 1]}
        # NorthEast square, W
        {
        "type": "linkage",
        "port": (1,1,6),
        "link": (0,1,2),
        "spin": (3, 4),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [1, 0]}
        # East square, N
        {
        "type": "linkage",
        "port": (1,0,0),
        "link": (1,1,4),
        "spin": (0, 1),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [1, 0]}
        # East square, W
        {
        "type": "linkage",
        "port": (1,0,6),
        "link": (0,0,2),
        "spin": (3, 4),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [1, 0]}
        # East square, S
        {
        "type": "linkage",
        "port": (1,0,4),
        "link": (1,-1,0),
        "spin": (1, 2),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [1, -1]}
        # SouthEast square, N
        {
        "type": "linkage",
        "port": (1,-1,0),
        "link": (1,0,4),
        "spin": (0, 1),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [1, -1]}
        # SouthEast square, W
        {
        "type": "linkage",
        "port": (1,-1,6),
        "link": (0,-1,2),
        "spin": (3, 4),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [1, -1]}
        # SouthEast square, NW
        {
        "type": "linkage",
        "port": (1,-1,7),
        "link": (0,0,3),
        "spin": (7, 8),
        "cost": 2,
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, -1]}
        # South square, N
        {
        "type": "linkage",
        "port": (0,-1,0),
        "link": (0,0,4),
        "spin": (0, 1),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, -1]}
        # South square, E
        {
        "type": "linkage",
        "port": (0,-1,2),
        "link": (1,-1,6),
        "spin": (1, 4),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [0, -1]}
        # South square, W
        {
        "type": "linkage",
        "port": (0,-1,6),
        "link": (-1,-1,2),
        "spin": (3, 4),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [-1, -1]}
        # SouthWest square, N
        {
        "type": "linkage",
        "port": (-1,-1,0),
        "link": (-1,0,4),
        "spin": (0, 1),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [-1, -1]}
        # SouthWest square, NE
        {
        "type": "linkage",
        "port": (-1,-1,1),
        "link": (0,0,5),
        "spin": (1, 8),
        "cost": 2,
        }
        {"seal": 20260906200320, "type": "data/python", "path": [-1, -1]}
        # SouthWest square, E
        {
        "type": "linkage",
        "port": (-1,-1,2),
        "link": (0,-1,6),
        "spin": (1, 4),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [-1, 0]}
        # West square, N
        {
        "type": "linkage",
        "port": (-1,0,0),
        "link": (-1,1,4),
        "spin": (0, 1),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [-1, 0]}
        # West square, E
        {
        "type": "linkage",
        "port": (-1,0,2),
        "link": (0,0,6),
        "spin": (1, 4),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [-1, 0]}
        # West square, S
        {
        "type": "linkage",
        "port": (-1,0,4),
        "link": (-1,-1,2),
        "spin": (1, 2),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [-1, 1]}
        # NorthWest square, E
        {
        "type": "linkage",
        "port": (-1,1,2),
        "link": (0,1,6),
        "spin": (1, 4),
        }
        {"seal": 20260906200320, "type": "data/python", "path": [-1, 1]}
        # NorthWest square, SE
        {
        "type": "linkage",
        "port": (-1,1,3),
        "link": (0,0,7),
        "spin": (3, 8),
        "cost": 2,
        }
        {"seal": 20260906200320, "type": "data/python", "path": [-1, 1]}
        # NorthWest square, S
        {
        "type": "linkage",
        "port": (-1,1,4),
        "link": (-1,0,0),
        "spin": (1, 2),
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

    def test_marker_from_json(self):
        text = textwrap.dedent("""
        {"seal": 20260906200320, "type": "application/json", "path": []}
        {
        "type": "marking",
        "name": "world_focus",
        "view": [0, 0],
        "face": [0, 1],
        "span": 12,
        "tick": 0,
        "memo": {
            "[0, 0]": 3
        }
        }
        """).lstrip()
        adaptor = Multipart(
            factory={
                dict: UserDict, list: UserList, str: UserString, "marking": Marker
            }
        )
        items = list(adaptor.scan("\n".join(text.splitlines() + self.text.splitlines()[13:])))
        self.assertIsInstance(items[0]["payload"], Marker)
        self.assertIsInstance(items[0]["payload"], Marker)
        self.assertIsInstance(items[0]["payload"].memo, Counter)

        journal = Journal(adaptor, uri="test.rht")

    def test_marker_via_journal(self):
        adaptor = Multipart(
            factory={
                dict: UserDict, list: UserList, str: UserString, "marking": Marker
            }
        )
        items = list(adaptor.scan(self.text))
        journal = Journal(adaptor, uri="test.rht")

        self.assertIsInstance(items[0]["payload"], Marker)
        self.assertIsInstance(items[0]["payload"].face, tuple)
        self.assertIsInstance(items[0]["payload"].memo, Counter)
        self.assertIsInstance(list(items[0]["payload"].memo)[0], tuple)

        frame = journal.model[()]
        self.assertTrue(frame)
        self.assertIsInstance(frame, Frame)
        self.assertEqual(getattr(frame, "path"), ())

        element = frame[0]
        self.assertIs(getattr(element, "parent"), frame)
        self.assertIsInstance(element, Marker)

    def test_marker_jump(self):
        adaptor = Multipart(
            factory={
                dict: UserDict, list: UserList, str: UserString, "marking": Marker
            }
        )
        items = list(adaptor.scan(self.text))
        journal = Journal(adaptor, Travel, uri="test.rht")
        branches = journal.branches((0, 0))
        self.assertEqual(len(branches), 8)

        options = {pair[1].path: pair[0].spin for pair in branches}
        marker = journal.marking["world_focus"]

        self.assertIs(marker, journal.adaptor.data[()][0])
        self.assertIs(marker, journal.model[()][0])

        self.assertEqual(marker.tick, 0)

        path = (1, 1)
        with self.subTest(path=path):
            spin = options[path]
            rv = marker.jump(path, spin=spin)
            self.assertEqual(rv["tick"], 1)
            self.assertEqual(rv["face"], spin)

    def test_marker_move(self):
        adaptor = Multipart(
            factory={
                dict: UserDict, list: UserList, str: UserString, "marking": Marker
            }
        )
        items = list(adaptor.scan(self.text))
        journal = Journal(adaptor, Travel, uri="test.rht")

        marker = journal.marking["world_focus"]
        self.assertIs(marker, journal.adaptor.data[()][0])
        self.assertIs(marker, journal.model[()][0])

        path = (1, 1)
        with self.subTest(path=path):
            branches = journal.branches(marker.view)
            options = {pair[1].path: pair[0].spin for pair in branches}
            spin = options[path]
            rv = marker.move(path, spin=spin)
            self.assertEqual(rv["tick"], 1)
            self.assertEqual(rv["face"], spin)

            self.assertEqual(marker.tick, 1)
            self.assertEqual(marker.face, spin)
            self.assertEqual(marker.view, (1, 1))

        marker.twist = True
        path = (1, 0)
        with self.subTest(path=path):
            branches = journal.branches(marker.view)
            options = {pair[1].path: pair[0].spin for pair in branches}
            spin = options[path]
            rv = marker.move(path, spin=spin)
            self.assertEqual(rv["tick"], 2)
            self.assertEqual(rv["face"], (5, 8))  # 1/4 turn + 1/2 turn

            self.assertEqual(marker.tick, 2)
            self.assertEqual(marker.face, (5, 8))
            self.assertEqual(marker.view, (1, 0))

