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
import json
import pathlib
import shutil
import tempfile
import textwrap
import unittest

import busker
from busker.model.multipart import Multipart

from busker.model.test.test_travel import TravelTests


class MultipartTests(unittest.TestCase):

    def test_dump(self):
        doc = Multipart()
        doc.data[(0,)].append(UserDict(a=1, b=2, c=3))
        doc.data[(1,)].append(
            textwrap.dedent("""
            In the beginning...
            """)
        )
        doc.data[(2,)].append(
            textwrap.dedent("""
            And they lived happily ever after.
            """)
        )
        rv = str(doc).splitlines()
        for n in (0, 6, 10):
            with self.subTest(n=n):
                header = json.loads(rv[0])
                self.assertEqual(header.get("path", ()), [0,], header)

    def test_feed(self):
        text = textwrap.dedent("""
        {"seal": 2863490869328, "busker": "0.25.0", "type": "application/json"}
        {
        "port": 8080
        }
        {"seal": 2863490869328, "busker": "0.25.0", "type": "text/plain", "path": ["a", "b", "c"]}

        <A> Knock knock.
        <B> Who's there?
        {"seal": 2863490869328, "busker": "0.25.0", "type": "application/x-python"}
        print("Hello, World!")
        """).lstrip()
        doc = Multipart()
        # adapter = Multipart(factory={dict: UserDict, list: UserList, str: UserString})
        bits = list(doc.scan(text))
        self.assertEqual(len(bits), 3, bits)
        self.assertIsInstance(doc.data[()][0], dict)
        self.assertIsInstance(doc.data[("a", "b", "c")][0], str)
        self.assertIsInstance(doc.data[()][1], ast.AST)

    def test_feed_reject(self):
        for n, text in enumerate([
            textwrap.dedent("""
            {"seal": 2863490869328, "busker": "0.25.0", "type": "application/json"}
            """),  # Leading whitespace
            textwrap.dedent("""
            {{"seal": 2863490869328, "busker": "0.25.0", "type": "application/json"}
            """).lstrip(),
            textwrap.dedent("""
            {"seal": 2863490869328, "busker": "0.25.0", "type": "application/json"}}
            """).lstrip(),
            textwrap.dedent("""
            {"seal": 2863490869328, "busker": "0.25.0", "type": "application/json"}
            {
            "port": 8080
            }
            {"seal": "2863490869328", "busker": "0.25.0", "type": "text/plain"}

            <A> Knock knock.
            <B> Who's there?
            """).lstrip(),  # Mismatched seal
            textwrap.dedent("""
            {"seal": 2863490869328, "busker": "0.25.0", "type": "application/json"}
            {
            "port": 8080,  # This is not valid JSON
            }
            """).lstrip(),
        ]):
            with self.subTest(n=n, text=text):
                doc = Multipart()
                with self.assertLogs("busker.multipart", level="ERROR") as context:
                    bits = list(doc.scan(text))
                self.assertIn("ERROR", "\n".join(context.output))
                self.assertIn("Pos: ", "\n".join(context.output))

    def test_header(self):
        config = dict(port=8080)
        text = textwrap.dedent("""
        <A> Knock knock.
        <B> Who's there?
        """)
        code = ast.parse("print('Hello, World!')")
        doc = Multipart(config, text, code)
        self.assertIsInstance(doc.header, dict)
        self.assertTrue(doc.header.get("seal", None))
        self.assertEqual(doc.header.get("busker", None), busker.__version__)

        rv = str(doc)
        self.assertIn("'port': 8080", rv)
        self.assertIn("Knock knock.", rv)
        self.assertIn("Hello, World!", rv)

    def test_str(self):
        config = dict(port=8080)
        text = textwrap.dedent("""
        <A> Knock knock.
        <B> Who's there?
        """).rstrip()
        doc = Multipart(config, text)
        rv = str(doc)
        lines = rv.splitlines()
        self.assertEqual(len(lines), 6, rv)

    def test_tree(self):
        doc = Multipart(factory={dict: UserDict, list: UserList, str: UserString})
        list(doc.scan(TravelTests.texts[2]))
        rv = doc.tree
        self.assertIsInstance(rv, dict)
        self.assertEqual(("a", "b"), tuple(rv), rv)
        self.assertIn(0, rv["a"], rv)
        self.assertIn(1, rv["a"][0])
        self.assertIn(2, rv["a"][0][1])
        self.assertEqual(rv["a"][0][1][2]["goods"], {"tea", "biscuits", "milk"})
        self.assertIs(rv["a"][0][1][2].maps[1], doc.data[("a", 0, 1, 2)][0])

    def test_factory(self):
        text = textwrap.dedent("""
        {"seal": 2863490869328, "type": "application/json"}
        {
        "rank": 0
        }
        {"seal": 2863490869328, "type": "application/json", "path": ["a"]}
        {
        "rank": 0
        }
        {"seal": 2863490869328, "type": "application/json", "path": ["a"]}
        {
        "rank": 1
        }
        {"seal": 2863490869328, "type": "application/json", "path": ["a", "b"]}
        {
        "rank": 0
        }
        {"seal": 2863490869328, "type": "application/json", "path": ["a", "b"]}
        {
        "rank": 1
        }
        {"seal": 2863490869328, "type": "text/plain", "path": ["a", "b"]}
        Yesterday, upon the stair...
        """).lstrip()
        doc = Multipart()
        list(doc.scan(text))
        for k, seq in doc.data.items():
            with self.subTest(k=k):
                self.assertIsInstance(seq, list)
                self.assertTrue(seq)
                for i in seq:
                    with self.subTest(i=i):
                        self.assertTrue(i)
                        self.assertIsInstance(i, (dict, str))

        doc = Multipart(factory={dict: UserDict, list: UserList, str: UserString})
        list(doc.scan(text))
        for k, seq in doc.data.items():
            with self.subTest(k=k):
                self.assertIsInstance(seq, UserList)
                self.assertTrue(seq)
                for i in seq:
                    with self.subTest(i=i):
                        self.assertTrue(i)
                        self.assertIsInstance(i, (UserDict, UserString))
