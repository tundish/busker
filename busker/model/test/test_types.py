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

import unittest


from busker.model.types import Accumulator
from busker.model.types import Rank
from busker.model.types import Text


class AccumulatorTests(unittest.TestCase):

    def test_complex(self):
        memo = Accumulator()
        rv = memo["a"]
        self.assertIsInstance(rv, complex)
        self.assertEqual(rv, 0)
        self.assertFalse(rv)


class TextTests(unittest.TestCase):

    def test_ranking(self):
        data = [
            Text("<> Two"),
            Text("""
            <> One
            """, rank=Rank.PROLOGUE),
            Text("""
            <> Three
            """),
        ]
        items = sorted(data)
        self.assertEqual(
            [i.text for i in items],
            ["<> One\n", "<> Two", "<> Three\n"]
        )
