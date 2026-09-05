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
import unittest

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
        journal = Journal(adaptor, Search, Syntax, uri=pathlib.Path("test.rht"))
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
