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
import textwrap
import unittest

from busker.model.multipart import Multipart
from busker.model.plotline import Plotline


class PlotlineTests(unittest.TestCase):

    def setUp(self):
        text = textwrap.dedent("""
        {"mark": 2863490869328, "type": "application/json"}
        {
        "type": "context",
        "score": 0
        }
        {"mark": 2863490869328, "type": "application/json"}
        {
        "type": "actions",
        "params": [
            "marker": "$['marker']"
            "place": "$[*]['description']"
        ],
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

        """).lstrip()
        self.plot = Plotline.scan(text)

    def test_types(self):
        for key in ((), ("a",), ("a", "b")):
            with self.subTest(key=key):
                self.fail(self.plot.doc.data[key])

