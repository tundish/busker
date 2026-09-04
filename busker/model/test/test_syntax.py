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
from busker.model.plotline import Plotline
from busker.model.syntax import Syntax
from busker.model.types import Chain
from busker.model.types import Element
from busker.model.types import ElementType
from busker.model.types import Frame
from busker.model.types import Lens

from busker.model.test.test_plotline import PlotlineTests


class JournalTests(unittest.TestCase):

    def setUp(self):
        self.adaptor = Multipart(factory={dict: UserDict, list: UserList, str: UserString})

    @staticmethod
    def build_journal(text):
        adaptor = Multipart(factory={dict: UserDict, list: UserList, str: UserString})
        list(adaptor.scan(text))
        journal = Journal(adaptor, Syntax, uri=pathlib.Path("test.rht"))
        return journal

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
        text = PlotlineTests.texts[2] + action_text
        journal = self.build_journal(text)
        syntax = list(journal.registry[Lens])[0]
        rht = journal.model
        path = ("b", 1)
        actions = syntax.actions(path)
        self.assertIsInstance(actions, dict)
        rv = actions.get("drop off milk at work")
        self.assertIsInstance(rv, tuple)
        self.assertEqual(len(rv), 2)
        self.assertIsInstance(rv[0], Element)
        self.assertEqual(rv[0], rht[()][-2])
        self.assertEqual(rv[0].handler, rht[()][-1])
        self.assertEqual(rv[1], dict(goods="milk", place="work"))

        self.assertEqual(syntax.context(path).get("goods", None), {"crumpets", "milk"})
        code = compile(rv[0].handler, format(path), mode="exec")
        l = dict(rv[1], journal=journal, path=path)
        g = dict(logging=logging)
        with self.assertLogs(format(path), logging.DEBUG) as check:
            exec(code, locals=l, globals=g)

        self.assertTrue(check.output)
        self.assertIn("Removed goods 'milk' from context", check.output[0])
        self.assertEqual(rht.context(path).get("goods", None), {"crumpets"})
