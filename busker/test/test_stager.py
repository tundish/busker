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

import pprint
import textwrap
import unittest

from busker.stager import Stager


class StagerTests(unittest.TestCase):

    rules = [
        textwrap.dedent("""
        label = "Repo of the Unknown"
        realm = "rotu"

        [[puzzles]]
        name = "a"

        [puzzles.chain.completion]
        "b" = "Fruition.inception"

        [puzzles.chain.withdrawn]
        "e" = "Fruition.inception"

        [puzzles.chain.defaulted]
        "e" = "Fruition.inception"

        [puzzles.chain.cancelled]
        "e" = "Fruition.inception"

        [[puzzles]]
        name = "b"

        [puzzles.chain.completion]
        "c" = "Fruition.inception"

        [[puzzles]]
        name = "c"

        [puzzles.chain.completion]
        "d" = "Fruition.inception"

        [[puzzles]]
        name = "d"

        [[puzzles]]
        name = "e"

        [puzzles.chain.completion]
        "g" = "Fruition.inception"

        [puzzles.chain.defaulted]
        "f" = "Fruition.inception"

        [[puzzles]]
        name = "f"

        [[puzzles]]
        name = "g"
        """),
        textwrap.dedent("""
        label = "Rotu content update"
        realm = "rotu"

        [[puzzles]]
        name = "c"

        [puzzles.chain.withdrawn]
        "h" = "Fruition.inception"

        [[puzzles]]
        name = "h"

        [puzzles.chain.completion]
        "d" = "Fruition.inception"

        [puzzles.chain.withdrawn]
        "g" = "Fruition.inception"

        [[puzzles]]
        name = "d"

        [[puzzles]]
        name = "g"

        """),
        textwrap.dedent("""
        label = "Rotu with Zombies"
        realm = "rotu.ext.zombie"

        [[puzzles]]
        name = "a"

        [puzzles.chain.completion]
        "c" = "Fruition.inception"

        [puzzles.chain.withdrawn]
        "b" = "Fruition.inception"

        [[puzzles]]
        name = "b"

        [[puzzles]]
        name = "c"

        [puzzles.chain.completion]
        "d" = "Fruition.inception"

        [[puzzles]]
        name = "d"
        """),
    ]

    def test_strands(self):
        data = list(Stager.load(*self.rules))
        stager = Stager(data).prepare()

        self.assertIsInstance(stager.active, list)
        self.assertEqual(stager.active, [("rotu", "a"), ("rotu.ext.zombie", "a")])

        events = list(stager.terminate("rotu", "a", "completion"))
        self.assertEqual(events, [("rotu", "b", "Fruition.inception")])

        self.assertEqual(stager.active, [("rotu.ext.zombie", "a"), ("rotu", "b"), ("rotu", "e")])

    def test_spots(self):

        rule = textwrap.dedent("""
        label = "Hunt the Gnome"
        namespace = "hunt_the_gnome"

        [[puzzles]]
        name = "Get a shovel"
        type = "Exploration"

        [puzzles.init]
        Fruition = "inception"

        [puzzles.state.spot]
        patio = ["Patio"]
        garden = ["Garden"]
        car_park = ["Car Park"]

        [puzzles.selector]
        # See fnmatch module for match syntax
        paths = [
            "busker/demo/scenes/0[01234]/*.scene.toml",
            "busker/demo/scenes/24/*.scene.toml",
        ]

        [puzzles.chain.completion]
        "Bag of bait" = "Fruition.inception"

        [[puzzles.triples]]
        name = "garden_path"
        type = "Transit"
        states = ["exit.patio", "into.garden", "Traffic.flowing", 3]
        """)

        data = list(Stager.load(rule))
        self.assertTrue(data)
        pprint.pprint(data[0])
