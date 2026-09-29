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
import logging
import pathlib
import platform
import textwrap
import unittest

from busker.model.journal import Journal
from busker.model.multipart import Multipart
from busker.model.search import Search
from busker.model.descent import Descent
from busker.model.types import Chain
from busker.model.types import Element
from busker.model.types import ElementType
from busker.model.types import Lens

from busker.model.test.test_travel import TravelTests


class DescentTests(unittest.TestCase):

    @staticmethod
    def build_journal(text):
        adaptor = Multipart(factory={dict: UserDict, list: UserList, str: UserString})
        list(adaptor.scan(text))
        journal = Journal(adaptor, Search, Descent, uri=pathlib.Path("test.rht"))
        return journal

    def test_journal_context(self):
        journal = self.build_journal(TravelTests.texts[2])

        path = ("a", 0, 1, 2)
        for n in range(3):
            with self.subTest(path=path, n=n):
                rv = Descent.context(journal, path)
                self.assertIsInstance(rv, Chain)
                self.assertTrue(isinstance(i, Element) for i in rv.maps)
                self.assertEqual(rv["type"], ElementType.CONTEXT.value)
                self.assertEqual(rv["chord"], ("C", "F", "G"), journal.adaptor.data)
                self.assertEqual(rv["goods"], {"tea", "biscuits", "eggs", "milk"})
                self.assertEqual(rv["route"], ["home", "shop", "home", "work", "shop", "work", "home"], rv)

    @unittest.skipIf(platform.python_version() < "3.13", "new eval semantics")
    def test_compile_exec_action(self):
        action_text = textwrap.dedent("""
        {"seal": 127416676279376, "type": "data/python", "path": []}
        {
        "type": "handler",
        "description": "After visiting a path 3 times, discard one of the goods",
        "rank": 10,
        }
        {"seal": 127416676279376, "type": "code/python"}
        if not marker.memo[marker.mark].real % 3:
            random.shuffle(goods := context["goods"])
            logging.getLogger(format(marker.mark)).debug(f"Jumbled goods '{goods}'")
        {"seal": 127416676279376, "type": "data/python", "path": []}
        {
        "type": "handler",
        "description": "Play an extra note in the Wednesday chord",
        "rank": 5,
        "params": {
            "chord": "$['chord'][?@['day'] == 'Wednesday']",
        },
        }
        {"seal": 127416676279376, "type": "code/python"}
        if not marker.tick % 4:
            context = engine.journal.context(marker.mark)
            context["goods"].remove(goods)
            logging.getLogger(format(path)).debug(
                f"Played '{chord}' in context '{path}'"
            )
        """)
        text = TravelTests.texts[2] + action_text
        journal = self.build_journal(text)
        descent = list(journal.registry[Lens])[0]
        mark = ("b", 1)
        events = descent.events(mark)
        self.assertIsInstance(events, list)
        self.assertEqual(len(events), 2, events)
        rv = events[0]
        self.assertIsInstance(rv, Element)
        self.assertTrue(rv.handler)
        self.assertEqual(len(rv.grid), 1)
        self.assertEqual(rv.rank, 5)

        self.assertEqual(rv, journal.model[()][-2])
        self.assertEqual(rv.handler, journal.model[()][-1])
        self.assertEqual(rv, dict(goods="milk", place="work"))

        self.assertEqual(descent.context(journal, path).get("goods", None), {"crumpets", "milk"})
        code = compile(rv[0].handler, format(path), mode="exec")
        l = dict(rv[1], journal=journal, path=path)
        g = dict(logging=logging)
        with self.assertLogs(format(path), logging.DEBUG) as check:
            exec(code, locals=l, globals=g)

        self.assertTrue(check.output)
        self.assertIn("Removed goods 'milk' from context", check.output[0])
        self.assertEqual(descent.context(path).get("goods", None), {"crumpets"})
