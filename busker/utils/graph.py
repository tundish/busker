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


"""
This utility translates puzzles from stage files into an equivalent .dot graph

Usage:

    python -m utils.graph --label "Story strands" \
        scenes/*/*.stage.toml > stage_graph.dot

    dot -Tsvg stage_graph.dot > stage_graph.svg

"""

import argparse
from collections.abc import Generator
import pathlib
import pprint
import sys

from busker.stager import Stager


def back_bearing(value: str):
    return {
        "n": "s",
        "ne": "sw",
        "e": "w",
        "se": "nw",
        "s": "n",
        "sw": "ne",
        "w": "e",
        "nw": "se",
    }.get(value, "")


def load_rules(*paths: tuple[pathlib.Path]):
    for path in paths:
        text = path.read_text()
        print("Processed", pathlib.Path(path).resolve(), file=sys.stderr)
        yield from Stager.load(text)


def puzzle_graph(realm, puzzle: dict, indent="") -> Generator[str]:
    indents = [indent * n for n in range(4)]
    puzzle_id = f"cluster_{realm}_{puzzle['name']}"
    yield f'{indents[1]}subgraph "{puzzle_id}" {{'
    yield f"{indents[2]}node [shape = doubleoctagon];"
    yield f"{indents[2]}label=\"{puzzle['name']}\";"
    yield f'{indents[2]}cluster="true";'

    declared_states = set()
    for state in puzzle.get("selector", {}).get("states", []):
        state_value = state.split(".")[-1]
        declared_states.add(state_value)
        yield f'{indents[2]}"{puzzle_id}_{state}"[label="{state_value}"]'

    for item in puzzle.get("items", []):
        if item.get("type", "").lower() == "transit":
            states = {
                state[0]: state[2]
                for i in item.get("states", [])
                if isinstance(i, str)
                and (state := i.lower().partition("."))[1]
            }
            values = set(filter(
                None,
                (
                 state for key in ("exit", "home", "into", "spot")
                 if (state := states.get(key)) not in declared_states
                )
            ))
            for value in values:
                yield f'{indents[2]}"{puzzle_id}_spot.{value}"[label="{value}"]'

            if set(states).issuperset({"exit", "into"}):
                exit_id = f"{puzzle_id}_spot.{states['exit']}"
                into_id = f"{puzzle_id}_spot.{states['into']}"
                if item.get("layout", {}).get("compass", ""):
                    exit_port = item["layout"]["compass"]
                    into_port = back_bearing(exit_port)
                    yield f'{indents[2]}"{exit_id}" -- "{into_id}" [tailport="{exit_port}" headport="{into_port}"]'
                else:
                    yield f'{indents[2]}"{exit_id}" -- "{into_id}"'

    yield f"{indents[1]}}}"

    for state, transition in puzzle.get("chain", {}).items():
        for target, event in transition.items():
            yield  f'{indents[1]}"{puzzle_id}" -- "cluster_{realm}_{target}" [label="{state}"]'
    yield ""


def main(args):
    data = list(load_rules(*args.input))
    stager = Stager(rules=data)
    snapshot = stager.snapshot
    pprint.pprint(snapshot, sort_dicts=False, stream=sys.stderr)

    indent = " " * 4
    label = f'"{args.label}"' if args.label else ""
    lines = [
        f"graph {label} {{",
        f'{indent}layout = "fdp";',
        f'{indent}splines = "true";',
        f'{indent}packmode = "graph";',
        f'{indent}edge [labelfloat = true];',
        # f'{indent}dim = "10"',
        # f'{indent}sep = "4"',
        # f'{indent}esep = "12"',
        # f'{indent}overlap = "scale"',
        # f'{indent}clusterrank = "local"',
        ""
    ]
    for (realm, puzzle_name), puzzle in snapshot.items():
        realm = realm.replace(" ", "")
        lines.extend(list(puzzle_graph(realm, puzzle, indent=indent)))

    lines.append("}")
    if not args.input:
        print("No files processed.")
        return 2

    print(*lines, sep="\n", file=sys.stdout)
    print("Generated", len(lines), "lines of output.", file=sys.stderr)
    return 0


def parser():
    rv = argparse.ArgumentParser(__doc__)
    rv.add_argument(
        "--label", default="",
        help="Set a label for the graph."
    )
    rv.add_argument(
        "input", nargs="+", type=pathlib.Path,
        help="Set input file."
    )
    return rv


def run():
    p = parser()
    args = p.parse_args()
    rv = main(args)
    sys.exit(rv)


if __name__ == "__main__":
    run()
