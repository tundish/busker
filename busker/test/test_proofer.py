#!/usr/bin/env python3
#   encoding: utf-8

# This is part of the Busker library.
# Copyright (C) 2024 D E Haynes

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import pathlib
import tempfile
import textwrap
import tomllib
import unittest

from busker.proofer import Proofer


class ProoferTests(unittest.TestCase):

    def test_read_scene_not_found(self):
        with tempfile.TemporaryDirectory() as parent:
            path = pathlib.Path(parent).joinpath("null.scene.toml")
            script = Proofer.read_script(path)
        self.assertIsInstance(script, Proofer.Script)
        self.assertEqual(script.path, path)
        self.assertFalse(script.text)
        self.assertIsNone(script.tables)
        self.assertTrue(script.errors)

    def test_read_scene_invalid(self):
        with tempfile.TemporaryDirectory() as parent:
            path = pathlib.Path(parent).joinpath("invalid.scene.toml")
            path.write_text("]")
            script = Proofer.read_script(path)
        self.assertTrue(script)
        self.assertIn(1, script.errors)
        self.assertIsInstance(script.errors[1], tomllib.TOMLDecodeError)

    def test_parse_field_name(self):
        text = textwrap.dedent("""
        [ALICE]
        name = "Alice"

        [[_]]
        s='''
        <ALICE>Hey, {BORIS.name}!
        '''
        """).strip()
        fd, name = tempfile.mkstemp(suffix=".scene.toml", text=True)
        path = pathlib.Path(name)
        try:
            path.write_text(text)
            script = Proofer.read_script(path)
            script = Proofer.check_scene(script)
            self.assertTrue(script.errors, script)
            self.assertIn(6, script.errors)
            self.assertIn("BORIS", script.errors[6])
        finally:
            os.close(fd)
            path.unlink()

    def test_parse_role_name(self):
        text = textwrap.dedent("""
        [ALICE]
        name = "Alice"

        [[_]]
        s='''
        <BORIS>Hey, {ALICE.name}!
        '''
        """).strip()
        fd, name = tempfile.mkstemp(suffix=".scene.toml", text=True)
        path = pathlib.Path(name)
        try:
            path.write_text(text)
            script = Proofer.read_script(path)
            script = Proofer.check_scene(script)
            self.assertTrue(script.errors, script)
            self.assertIn(6, script.errors)
            self.assertIn("BORIS", script.errors[6])
        finally:
            os.close(fd)
            path.unlink()

    def test_parse_role_name_empty(self):
        text = textwrap.dedent("""
        [ALICE]
        name = "Alice"

        [[_]]
        s='''
        <>Hey, {ALICE.name}!
        '''
        """).strip()
        fd, name = tempfile.mkstemp(suffix=".scene.toml", text=True)
        path = pathlib.Path(name)
        try:
            path.write_text(text)
            script = Proofer.read_script(path)
            script = Proofer.check_scene(script)
            self.assertFalse(script.errors, script)
        finally:
            os.close(fd)
            path.unlink()

    def test_parse_role_directive(self):
        text = textwrap.dedent("""
        [ALICE]
        name = "Alice"

        [[_]]
        s='''
        <BORIS:proposing>Hey, {ALICE.name}!
        '''
        """).strip()
        fd, name = tempfile.mkstemp(suffix=".scene.toml", text=True)
        path = pathlib.Path(name)
        try:
            path.write_text(text)
            script = Proofer.read_script(path)
            script = Proofer.check_scene(script)
            self.assertTrue(script.errors, script)
            self.assertIn(6, script.errors)
            self.assertIn("BORIS", script.errors[6])
            self.assertNotIn("proposing", script.errors[6])
        finally:
            os.close(fd)
            path.unlink()

    def test_parse_role_mode(self):
        text = textwrap.dedent("""
        [ALICE]
        name = "Alice"

        [[_]]
        s='''
        <BORIS:whispers>Hey, {ALICE.name}!
        '''
        """).strip()
        fd, name = tempfile.mkstemp(suffix=".scene.toml", text=True)
        path = pathlib.Path(name)
        try:
            path.write_text(text)
            script = Proofer.read_script(path)
            script = Proofer.check_scene(script)
            self.assertTrue(script.errors, script)
            self.assertIn(6, script.errors)
            self.assertIn("BORIS", script.errors[6])
            self.assertNotIn("whispers", script.errors[6])
        finally:
            os.close(fd)
            path.unlink()
