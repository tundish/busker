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

import textwrap
import unittest

from busker.engine.marker import Marker
from busker.engine.mechanism import Mechanism


class MechanismTests(unittest.TestCase):

    def setUp(self):
        self.text = textwrap.dedent("""
        <#!>
        1. One
        2. Two
        3. Tri

        <> Four

        <#!>
        1. A
        2. B
        3. C

        <> D
        """).lstrip()

    def test_split_cues(self):
        mechanism = Mechanism()
        cues = mechanism.split_cues(self.text)
        self.assertEqual(len(cues), 4)
        self.assertTrue(all(cue[0] == "<" for cue in cues))

    def test_rotate_cue(self):
        mechanism = Mechanism()
        marker = Marker(name="test_marker")
        for n, cue in enumerate(mechanism.split_cues(self.text)):
            with self.subTest(n=n, cue=cue):
                rv = mechanism.rotate_cue(cue, marker=marker)
                self.assertTrue(rv[0] == "<")
                self.assertIn(["One", "Four", "B", "D"][n], rv)
