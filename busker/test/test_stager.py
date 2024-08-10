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

import enum
import graphlib
import itertools
import operator
import pprint
import textwrap
import tomllib
import unittest

class Strand:

    # TODO: Validation of TOML

    def __init__(self, rules=[]):
        self.strands = {
            realm: {strand["label"]: strand for strand in strands}
            for realm, strands in itertools.groupby(
                sorted(rules, key=operator.itemgetter("realm")),
                key=operator.itemgetter("realm")
            )
        }

    @staticmethod
    def active(rules: list):
        """
        for key, group in itertools.groupby(
            sorted(rules, key=operator.itemgetter("realm")),
            key=operator.itemgetter("realm")
        ):
            yield (key, list(group))

        """

    @staticmethod
    def sorter(graph=None):
        return graphlib.TopologicalSorter(graph)


class StagerTests(unittest.TestCase):

    def test_strand(self):
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
        data = [tomllib.loads(rule) for rule in rules]
        pprint.pprint(data, indent=4, sort_dicts=False)

        strand = Strand(data)
        print(strand.strands)
        active = Strand.active(data)
        self.assertIsInstance(active, dict)
        self.assertEqual([("rotu", "a"), ("rotu.ext.zombie", "a")], list(active.keys()))

    def test_synch(self):

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

        data = tomllib.loads(rule)
        self.fail(data)
