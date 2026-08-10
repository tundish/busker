#!/usr/bin/env python
#   encoding: utf-8

# Copyright (C) 2025 D E Haynes
# This file is part of spiki.

# Spiki is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# Spiki is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with spiki.
# If not, see <https://www.gnu.org/licenses/>.

import pathlib
import shutil
import tempfile
import textwrap
import unittest

import spiki
from spiki.multipart import Multipart


class MultipartTests(unittest.TestCase):

    def setUp(self):
        self.path = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.path)

    def test_root_regex(self):
        text = textwrap.dedent("""
        {"mark": 2863490869328, "spiki": "0.25.0", "type": "application/json"}
        {
        "port": 8080
        }
        {"mark": 2863490869328, "spiki": "0.25.0", "type": "text/plain"}

        <A> Knock knock.
        <B> Who's there?
        """).lstrip()
        doc = Multipart()
        bits = list(doc.feed(text))
        self.assertEqual(len(bits), 2, bits)

    def test_root_regex_reject(self):
        for n, text in enumerate([
            textwrap.dedent("""
            {"mark": 2863490869328, "spiki": "0.25.0", "type": "application/json"}
            """),  # Leading whitespace
            textwrap.dedent("""
            {{"mark": 2863490869328, "spiki": "0.25.0", "type": "application/json"}
            """).lstrip(),
            textwrap.dedent("""
            {"mark": 2863490869328, "spiki": "0.25.0", "type": "application/json"}}
            """).lstrip(),
            textwrap.dedent("""
            {"mark": 2863490869328, "spiki": "0.25.0", "type": "application/json"}
            {
            "port": 8080
            }
            {"mark": "2863490869328", "spiki": "0.25.0", "type": "text/plain"}

            <A> Knock knock.
            <B> Who's there?
            """).lstrip(),  # Mismatched mark
            textwrap.dedent("""
            {"mark": 2863490869328, "spiki": "0.25.0", "type": "application/json"}
            {
            "port": 8080,  # This is not valid JSON
            }
            """).lstrip(),
        ]):
            with self.subTest(n=n, text=text):
                doc = Multipart()
                with self.assertLogs("spiki.multipart", level="ERROR") as context:
                    bits = list(doc.feed(text))
                self.assertIn("ERROR", "\n".join(context.output))
                self.assertIn("Pos: ", "\n".join(context.output))

    def test_simple(self):
        config = dict(port=8080)
        text = textwrap.dedent("""
        <A> Knock knock.
        <B> Who's there?
        """)
        doc = Multipart(config, text)
        self.assertIsInstance(doc.header, dict)
        self.assertTrue(doc.header.get("mark", None))
        self.assertEqual(doc.header.get("spiki", None), spiki.__version__)
        print(f"{doc.data=}")

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
