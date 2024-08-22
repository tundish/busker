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


from collections import Counter
from collections import defaultdict
from collections.abc import Generator
import enum
import graphlib
import itertools
import operator
import tomllib
import warnings


class Stager:

    @staticmethod
    def load(*rules: tuple[str]) -> Generator[dict]:
        witness = Counter()
        for n, rule in enumerate(rules):
            try:
                data = tomllib.loads(rule)
            except tomllib.TOMLDecodeError as e:
                warnings.warn("Invalid stage file: {e!s}")
                yield {}

            if not isinstance(data.get("puzzles"), list):
                warnings.warn(f"No puzzles detected in rule {n}")
            elif not set(data.keys()).issuperset({"label", "realm"}):
                warnings.warn("Every strand needs a 'label' and a 'realm'")

            if any(puzzle.get("init") for puzzle in data["puzzles"]):
                witness["init"] += 1

            yield data

        if not witness["init"]:
            warnings.warn("At least one puzzle must contain an 'init' table")

    @staticmethod
    def layout(item: dict, key=None) -> dict:
        compass = next(
            (parts[-1] for i in item.get("states", [])
             if (parts := i.lower().split("."))[0] == "compass"
            ),
            "_"
        )
        return dict(id=key, compass=compass)

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

    @property
    def snapshot(self) -> dict[tuple[str, str], dict]:
        realms = {
            realm: list(sorter.static_order()) or [
                puzzle.get("name")
                for strand in self.realms[realm].values()
                for puzzle in strand.get("puzzles", [])
                if puzzle.get("name")
            ]
            for realm, sorter in self.strands.items()
        }
        return {
            (realm, name): self.gather_puzzle(realm, name)
            for realm, names in realms.items()
            for name in names
        }

    def gather_state(self, state="spot") -> dict[str, list]:
        rv = defaultdict(list)
        for realm, strands in self.realms.items():
            for strand in strands.values():
                for puzzle in strand.get("puzzles", []):
                    table = puzzle.get("state", {}).get(state, {})
                    for key, values in table.items():
                        values = [values] if not isinstance(values, list) else values
                        rv[key].extend([v for v in values if v not in rv[key]])
        return rv

    def gather_puzzle(self, realm, name) -> dict:
        rv = {}
        items = {}
        paths = []
        states = []
        for s, strand in enumerate(self.realms.get(realm, {}).values()):
            for p, puzzle in enumerate(strand.get("puzzles", [])):
                if puzzle.get("name") == name:
                    rv["name"] = name
                    rv["type"] = puzzle.get("type", rv.get("type"))
                    rv["state"] = puzzle.get("state", {}).copy()
                    rv.setdefault("init", {}).update(puzzle.get("init", {}))
                    rv["chain"] = puzzle.get("chain", {}).copy()

                    items.update({
                        i.get("name", (s, p, n)): dict(i, layout=self.layout(i, key=(s, p, n)))
                        for n, i in enumerate(puzzle.get("items", []))
                    })
                    paths.extend(i for i in puzzle.get("selector", {}).get("paths", []) if i not in paths)
                    states.extend(i for i in puzzle.get("selector", {}).get("states", []) if i not in states)

        rv["selector"] = dict(paths=paths, states=states)
        rv["items"] = list(items.values())
        return rv

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
                    for target, events in puzzle.get("chain", {}).get(verdict, {}).items():
                        events = [events] if not isinstance(events, list) else events
                        for event in events:
                            yield (realm, target, event)

        self.strands[realm].done(name)
        self._active.remove((realm, name))
        self._active.extend(
            [(realm, name) for realm, strand in self.strands.items() for name in strand.get_ready()]
        )

