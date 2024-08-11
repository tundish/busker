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


from collections.abc import Generator
import enum
import graphlib
import itertools
import operator
import tomllib
import warnings


class Stager:

    @staticmethod
    def load(*rules: tuple[str]):
        for rule in rules:
            data = tomllib.loads(rule)
            if not isinstance(data.get("puzzles"), list):
                warnings.warn("No puzzles detected")
            elif not any(puzzle.get("init") for puzzle in data["puzzles"]):
                warnings.warn("At least one puzzle must contain an 'init' table")
            yield data

    def __init__(self, rules=[]):
        self._active = []

        self.realms = {
            realm: {strand["label"]: strand for strand in strands}
            for realm, strands in itertools.groupby(
                sorted(rules, key=operator.itemgetter("realm")),
                key=operator.itemgetter("realm")
            )
        }
        self.strands = {
            realm: graphlib.TopologicalSorter()
            for realm in self.realms
        }

        for realm, strands in self.realms.items():
            for strand in strands.values():
                for puzzle in strand.get("puzzles", []):
                    for table in puzzle.get("chain", {}).values():
                        for target in table.keys():
                            self.strands[realm].add(target, puzzle["name"])

    def prepare(self):
        for strand in self.strands.values():
            strand.prepare()

        self._active = [
            (realm, name) for realm, strand in self.strands.items() for name in strand.get_ready()
        ]
        return self

    @property
    def active(self):
        return self._active

    def terminate(self, realm: str, name: str, verdict: str) -> Generator[tuple[str, str, str]]:
        for strand in self.realms[realm].values():
            for puzzle in strand.get("puzzles", []):
                if puzzle.get("name") == name:
                    for target, event in puzzle.get("chain", {}).get(verdict, {}).items():
                        yield (realm, target, event)

        self.strands[realm].done(name)
        self._active.remove((realm, name))
        self._active.extend(
            [(realm, name) for realm, strand in self.strands.items() for name in strand.get_ready()]
        )

