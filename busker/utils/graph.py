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
#! /usr/bin/env python
# encoding: utf-8


"""
This utility translates a graph defined in a CFN file to an equivalent .dot

Usage:

    python -m utils.graph --label-graph "Story strands" --digraph \
        scenes/*/*.stage.toml > stage_graph.dot

    dot -Tsvg stage_graph.dot > stage_graph.svg

"""

import argparse
from collections import namedtuple
import dataclasses
import fileinput
import functools
import pathlib
import pprint
import re
import sys
import tomllib

from busker.stager import Stager


def load_rules(*paths: tuple[pathlib.Path]):
    for path in paths:
        text = path.read_text()
        print("Processed", pathlib.Path(path).resolve(), file=sys.stderr)
        yield from Stager.load(text)

"""
graph strand_0 {
subgraph realm_00 {
    subgraph cluster_puzzle_000 {
    node [shape = doubleoctagon];
    spot01[label="drive"]
    spot02[label="patio"]
    spot01:se -- spot02:nw;
    }
}

subgraph realm2_00 {

    subgraph cluster_puzzle_001 {
    node [shape = doubleoctagon];
    spot03[label="garden"]
    spot02:e -- spot03:w;
    }
}
}
"""

def main(args):
    data = list(load_rules(*args.input))
    stager = Stager(rules=data)
    snapshot = stager.snapshot
    pprint.pprint(snapshot, sort_dicts=False, stream=sys.stderr)

    if not args.input:
        print("No files processed.")
        return 2

    lines = list()
    print(*lines, sep="\n", file=sys.stdout)
    print("Generated", len(lines), "lines of output.", file=sys.stderr)


def parser():
    rv = argparse.ArgumentParser(__doc__)
    rv.add_argument(
        "--label-graph", default=None,
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
