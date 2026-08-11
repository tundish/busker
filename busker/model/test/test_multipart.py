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
import pathlib
import shutil
import tempfile
import textwrap
import unittest

import busker
from busker.model.multipart import Multipart


class MultipartTests(unittest.TestCase):

    def test_types(self):
        doc = Multipart()
        doc.data[()].append(UserDict(a=1, b=2, c=3))
        doc.data[(0)].append(
            textwrap.dedent("""
            In the beginning...
            """)
        )
        doc.data[(2)].append(
            textwrap.dedent("""
            And they lived happily ever after.
            """)
        )
        rv = str(doc)
        self.assertTrue(rv)

    def test_root_regex(self):
        text = textwrap.dedent("""
        {"mark": 2863490869328, "busker": "0.25.0", "type": "application/json"}
        {
        "port": 8080
        }
        {"mark": 2863490869328, "busker": "0.25.0", "type": "text/plain", "path": "a.b.c"}

        <A> Knock knock.
        <B> Who's there?
        {"mark": 2863490869328, "busker": "0.25.0", "type": "text/x-python"}
        print("Hello, World!")
        """).lstrip()
        doc = Multipart()
        bits = list(doc.feed(text))
        self.assertEqual(len(bits), 3, bits)
        self.assertIsInstance(doc.data[()][0], dict)
        self.assertIsInstance(doc.data[("a", "b", "c")][0], str)
        self.assertIsInstance(doc.data[()][1], ast.AST)

    def test_root_regex_reject(self):
        for n, text in enumerate([
            textwrap.dedent("""
            {"mark": 2863490869328, "busker": "0.25.0", "type": "application/json"}
            """),  # Leading whitespace
            textwrap.dedent("""
            {{"mark": 2863490869328, "busker": "0.25.0", "type": "application/json"}
            """).lstrip(),
            textwrap.dedent("""
            {"mark": 2863490869328, "busker": "0.25.0", "type": "application/json"}}
            """).lstrip(),
            textwrap.dedent("""
            {"mark": 2863490869328, "busker": "0.25.0", "type": "application/json"}
            {
            "port": 8080
            }
            {"mark": "2863490869328", "busker": "0.25.0", "type": "text/plain"}

            <A> Knock knock.
            <B> Who's there?
            """).lstrip(),  # Mismatched mark
            textwrap.dedent("""
            {"mark": 2863490869328, "busker": "0.25.0", "type": "application/json"}
            {
            "port": 8080,  # This is not valid JSON
            }
            """).lstrip(),
        ]):
            with self.subTest(n=n, text=text):
                doc = Multipart()
                with self.assertLogs("busker.multipart", level="ERROR") as context:
                    bits = list(doc.feed(text))
                self.assertIn("ERROR", "\n".join(context.output))
                self.assertIn("Pos: ", "\n".join(context.output))

    def test_simple(self):
        config = dict(port=8080)
        text = textwrap.dedent("""
        <A> Knock knock.
        <B> Who's there?
        """)
        code = ast.parse("print('Hello, World!')")
        doc = Multipart(config, text, code)
        self.assertIsInstance(doc.header, dict)
        self.assertTrue(doc.header.get("mark", None))
        self.assertEqual(doc.header.get("busker", None), busker.__version__)

        rv = str(doc)
        self.assertIn('"port": 8080', rv)
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
        self.assertEqual(len(lines), 8, rv)
