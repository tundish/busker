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
import pathlib
from types import SimpleNamespace
import unittest

from busker.model.descent import Descent
from busker.model.journal import Journal
from busker.model.multipart import Multipart
from busker.model.search import Search
from busker.model.syntax import Syntax
from busker.model.types import ElementType
from busker.model.types import Frame

from busker.model.test.test_travel import TravelTests


class SearchTests(unittest.TestCase):

    @staticmethod
    def build_journal(text):
        adaptor = Multipart(factory={dict: UserDict, list: UserList, str: UserString})
        list(adaptor.scan(text))
        journal = Journal(adaptor, Descent, Search, Syntax, uri=pathlib.Path("test.rht"))
        return journal

    def test_search_context_key(self):
        journal = self.build_journal(TravelTests.texts[2])
        context = journal.context(("b", 1))
        self.assertIsInstance(context.maps[0].parent, Frame)

        rv = journal.search("$['day']", context)
        self.assertEqual(rv, ["Wednesday"])

    def test_search_context_attribute(self):
        journal = self.build_journal(TravelTests.texts[2])
        context = journal.context(("b", 1))
        self.assertEqual(context.maps[0].type.value, ElementType.CONTEXT.value)

        rv = journal.search("$.maps[0].type.value", context)
        self.assertEqual(rv, ["context"])

    def test_marker_path(self):
        marker = SimpleNamespace(mark=("stage", "floor"))
        data = {
            "type": "context",
            "entities": {
                ("stage", "floor"): [
                    {"names": ["Can", "Beer can"], "types": {"junk", "can"}, "states": {"seen": False, "held": False}, "aspects": ["empty", "crumpled", "slightly sticky"]},
                    {"names": ["Can", "Beer can"], "types": {"junk", "can"}, "states": {"seen": False, "held": False}, "aspects": ["empty", "charred"]},
                    {"names": ["Can", "Beer can"], "types": {"junk", "can"}, "states": {"seen": False, "held": False}, "aspects": ["empty", "crumpled"]},
                    {"names": ["Pack of Rizlas", "Pack of Cigarette papers"], "types": {"junk"}, "states": {"seen": False, "held": False}, "aspects": ["damp", "unusable"]}
                ],
                ("stage", "dustbin"): [
                    {"names": ["Can", "Bean can"], "types": {"junk", "can"}, "states": {"seen": False, "held": False}, "aspects": ["empty", "crumpled", "slightly sticky"]},
                    {"names": ["Can", "Soup can"], "types": {"junk", "can"}, "states": {"seen": False, "held": False}, "aspects": ["empty", "jagged"]},
                ],
                ("stage", "inventory"): [
                    {"names": ["Knife", "Penknife"], "types": {"tool"}, "states": {"seen": True, "held": True}, "aspects": ["small", "sharp"]}
                ],
            }
        }
        selector = Search(None)
        query = "$['entities'][?#==_.mark][?@['types'] contains 'can']"
        rv = selector.search(query, data, filter_context=marker)
        self.assertEqual(len(rv), 3)
        self.assertTrue(all("Beer can" in i["names"] for i in rv), rv)
