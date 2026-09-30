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
import random
import textwrap
import unittest

from busker.engine.engine import Engine
from busker.engine.marker import Marker
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
            taken = context["goods"].pop()
            logging.getLogger(format(marker.mark)).debug(f"Removed {taken} from set of goods")
        {"seal": 127416676279376, "type": "data/python", "path": []}
        {
        "type": "handler",
        "description": "Play an extra note in every fourth chord",
        "rank": 5,
        }
        {"seal": 127416676279376, "type": "code/python"}
        if not marker.tick % 4:
            logger = logging.getLogger(format(marker.mark))
            try:
                chord = context["chord"]
            except KeyError as err:
                logger.warning(f"{chord=}")
            else:
                extended = (*chord, chord[0])
                logger.debug(f"Playing '{extended}' in context '{marker.mark}'")
        """)
        text = TravelTests.texts[2] + action_text
        journal = self.build_journal(text)
        engine = Engine(journal)
        descent = list(journal.registry[Lens])[0]
        marker = Marker(name="Test", mark=("b", 1))
        events = descent.events(marker.mark)
        self.assertIsInstance(events, list)
        self.assertEqual(len(events), 2, events)

        rv = events[0]
        self.assertIsInstance(rv, Element)
        self.assertTrue(rv.handler)
        self.assertEqual(rv.rank, 5)

        self.assertEqual(rv, journal.model[()][-2])
        self.assertEqual(rv.handler, journal.model[()][-1])

        self.assertEqual(descent.context(marker.mark).get("chord", None), ("C", "F", "G"))
        code = compile(rv.handler, format(marker.mark), mode="exec")

        context = descent.context(marker.mark)
        l = dict(engine=engine, context=context, marker=marker)
        g = dict(logging=logging, random=random)
        with self.assertLogs(format(marker.mark), logging.DEBUG) as check:
            exec(code, locals=l, globals=g)

        self.assertTrue(check.output)
        self.assertIn("Playing '('C', 'F', 'G', 'C')'", check.output[0])

        rv = events[1]
        self.assertIsInstance(rv, Element)
        self.assertTrue(rv.handler)
        self.assertEqual(rv.rank, 10)

        self.assertEqual(rv, journal.model[()][-4])
        self.assertEqual(rv.handler, journal.model[()][-3])

        code = compile(rv.handler, format(marker.mark), mode="exec")
        context = descent.context(marker.mark)
        goods = context["goods"].copy()
        l = dict(engine=engine, context=context, marker=marker)
        g = dict(logging=logging, random=random)
        with self.assertLogs(format(marker.mark), logging.DEBUG) as check:
            exec(code, locals=l, globals=g)

        missing = goods - context["goods"]
        self.assertTrue(missing)
        self.assertTrue(check.output)
        self.assertIn(missing.pop(), check.output[0])
