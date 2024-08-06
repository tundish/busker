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

import textwrap
import tomllib
import unittest


class StagerTests(unittest.TestCase):

    def test_synch(self):

        stage = textwrap.dedent("""
        [[puzzles]]
        [[puzzles.fruition]]
        completion = {puzzle_b = "fruition.inception"}

        [[puzzles.transits]]
        # named transits might be the thing
        name = "garden_path"
        type = "Transit"
        states = ["exit.patio", "into.garden", "Traffic.flowing", 3]
        """)

        data = tomllib.loads(stage)
        self.fail(data)
