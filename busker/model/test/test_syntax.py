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
from busker.model.syntax import Syntax
from busker.model.types import Chain
from busker.model.types import Element
from busker.model.types import ElementType
from busker.model.types import Lens

from busker.model.test.test_travel import TravelTests


class SyntaxTests(unittest.TestCase):

    @staticmethod
    def build_journal(text):
        adaptor = Multipart(factory={dict: UserDict, list: UserList, str: UserString})
        list(adaptor.scan(text))
        journal = Journal(adaptor, Syntax, uri=pathlib.Path("test.rht"))
        return journal

    def test_journal_context(self):
        journal = self.build_journal(TravelTests.texts[2])

        path = ("a", 0, 1, 2)
        for n in range(3):
            with self.subTest(path=path, n=n):
                rv = journal.context(path)
                self.assertIsInstance(rv, Chain)
                self.assertTrue(isinstance(i, Element) for i in rv.maps)
                self.assertEqual(rv["type"], ElementType.CONTEXT.value)
                self.assertEqual(rv["chord"], ("C", "F", "G"), journal.adaptor.data)
                self.assertEqual(rv["goods"], {"tea", "biscuits", "eggs", "milk"})
                self.assertEqual(rv["route"], ["home", "shop", "home", "work", "shop", "work", "home"], rv)

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
        text = TravelTests.texts[2] + action_text
        journal = self.build_journal(text)
        syntax = list(journal.registry[Lens])[0]
        path = ("b", 1)
        actions = syntax.actions(path)
        self.assertIsInstance(actions, dict)
        rv = actions.get("drop off milk at work")
        self.assertIsInstance(rv, tuple)
        self.assertEqual(len(rv), 2)
        self.assertIsInstance(rv[0], Element)
        self.assertEqual(rv[0], journal.model[()][-2])
        self.assertEqual(rv[0].handler, journal.model[()][-1])
        self.assertEqual(rv[1], dict(goods="milk", place="work"))

        self.assertEqual(syntax.context(path).get("goods", None), {"crumpets", "milk"})
        code = compile(rv[0].handler, format(path), mode="exec")
        l = dict(rv[1], journal=journal, path=path)
        g = dict(logging=logging)
        with self.assertLogs(format(path), logging.DEBUG) as check:
            exec(code, locals=l, globals=g)

        self.assertTrue(check.output)
        self.assertIn("Removed goods 'milk' from context", check.output[0])
        self.assertEqual(syntax.context(path).get("goods", None), {"crumpets"})
