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


RGBA = namedtuple("RGBA", ["r", "g", "b", "a"], defaults=(255,))
Arc = namedtuple(
    "Arc",
    ["label", "node", "target", "source", "weight", "color", "fill", "stroke"],
    defaults=(None, 1.0, RGBA(0, 0, 0), RGBA(0, 0, 0), RGBA(0, 0, 0))
)


@dataclasses.dataclass(eq=False)
class Node:

    name: str

    label: str = None
    weight: float = 1.0
    arcs: list[Arc] = dataclasses.field(default_factory=list)
    data: dict = None
    parent: object = None
    color: RGBA = RGBA(0, 0, 0)
    fill: RGBA = RGBA(0, 0, 0)
    stroke: RGBA = RGBA(0, 0, 0)

    def __post_init__(self):
        self.label = self.label or self.name

    @property
    def rank(self):
        return self.name.count(".")


class Model:

    @classmethod
    def loads(cls, text):
        data = tomllib.loads(text)
        return cls(text, data)

    @staticmethod
    def is_arc(table):
        return set(table.keys()).intersection({"source", "target"})

    def __init__(self, text, data, args=argparse.Namespace()):
        self.text = text
        self.data = data
        self.args = args
        self.table_finder = re.compile("\\[\\s*([\\.\\w]+)\\s*\\]")

    @property
    def graphs(self):
        """Experimental. Used to mask data by storing a list of the graphs they appear in."""
        return {
            i for table, k, v in self.walk()
            for i in (v if isinstance(v, list) else [v])
            if k == "graphs"
        }

    def walk(self, data=None, parent=None):
        data = data or self.data
        for k, v in data.items():
            if v and isinstance(v, dict):
                yield from self.walk(data=v, parent=data)
            else:
                yield parent, k, v

    @property
    @functools.cache
    def tables(self):
        rv = {}
        for path in self.table_finder.findall(self.text):
            keys = path.split(".")
            data = self.data
            for k in keys:
                data = data[k]
            rv[path] = data
        return rv

    @property
    @functools.cache
    def nodes(self):
        rv = {}
        arcs = {}
        fields = {i.name for i in dataclasses.fields(Node)}
        for name, table in self.tables.items():
            if self.is_arc(table):
                arcs[name] = table
                continue

            colours = {attr: RGBA(**table[attr]) for attr in ("color", "fill", "stroke") if attr in table}
            kwargs = dict({k: v for k, v in table.items() if k in fields}, **colours)
            node = Node(name, **kwargs)
            node.data = table
            if "." in name:
                paths = name.split(".")
                for gen in range(1, len(paths)):
                    last = ".".join(paths[:-gen])
                    if last in self.tables:
                        node.parent = last

            rv[name] = node

        for name, table in arcs.items():
            parent, dot, label = name.rpartition(".")
            kwargs = {attr: RGBA(**table[attr]) for attr in ("color", "fill", "stroke") if attr in table}
            arc = Arc(
                table.get("label", label),
                node=parent or None,
                target=table.get("target"),
                weight=table.get("weight", 1.0),
                **kwargs
            )
            try:
                rv[parent].arcs.append(arc)
            except AttributeError:
                print(
                    "Arc '", name, "' expects a Node for '", parent, "'.",
                    sep="", file=sys.stderr
                )
            except KeyError:
                print(
                    "No Node '", parent, "' for Arc '", name, "'.",
                    sep="", file=sys.stderr
                )

        return rv

    @functools.cache
    def children(self, name):
        return [
            k for k, v in self.nodes.items()
            if k != name and k.startswith(name)
        ]

    def subgraphs(self, parents=None):
        parents = parents or [v for v in self.nodes.values() if not v.parent]
        for p in parents:
            yield p
            children = [self.nodes[c] for c in self.children(p.name)]
            if children:
                yield from self.subgraphs(children)
                yield None

    def arcs(self):
        links = [
            (".".join(name.split(".")[:-1]), name)
            for name in self.tables if "." in name
        ]
        for parent, name in links:
            p = self.table(parent)
            t = self.table(name)
            if parent != name:
                if self.is_arc(t):
                    pass
                else:
                    yield p.get("label", parent), t.get("label", name)

    def to_cluster(self, name="model", label=None, directed=True, strict=True):
        label = label or name
        arc_style = "->" if directed else "--"

        yield f"{'strict ' if strict else ''}{'digraph' if directed else 'graph'} {name} {{"
        yield f'    label="{label}"'
        for node in self.subgraphs():
            if node is None:
                yield ""
                yield "}"
            elif self.children(node.name):
                node_name = node.name.lower().replace(".", "_")
                yield ""
                yield f"subgraph cluster_{node_name} {{"
                yield f'    label="{node.label}"'
                yield f"    weight={node.weight:.2f}"
                yield ""
            else:
                node_hash = hash(node)
                yield (
                    f"{node_hash}"
                    f' ['
                    f' label="{node.label}", weight={node.weight:.02f}'
                    f' color="#{node.stroke.r:02x}{node.stroke.g:02x}{node.stroke.b:02x}{node.stroke.a:02x}"'
                    f' fontcolor="#{node.color.r:02x}{node.color.g:02x}{node.color.b:02x}"'
                    f' fillcolor="#{node.fill.r:02x}{node.fill.g:02x}{node.fill.b:02x}"'
                    f' ]'
                )


        yield ""

        for node in self.nodes.values():
            node_hash = hash(node)
            for arc in node.arcs:
                target_hash = hash(self.nodes[arc.target])
                yield (
                    f"{node_hash} {arc_style} {target_hash}"
                    f' ['
                    f' label="{arc.label}", weight={arc.weight:.02f}'
                    f' color="#{arc.stroke.r:02x}{arc.stroke.g:02x}{arc.stroke.b:02x}"'
                    f' fontcolor="#{arc.color.r:02x}{arc.color.g:02x}{arc.color.b:02x}"'
                    f' fillcolor="#{arc.fill.r:02x}{arc.fill.g:02x}{arc.fill.b:02x}"'
                    f' ]'
                )
        yield ""
        yield "}"

    def to_dot(self, name="model", label=None, directed=True, strict=True):
        label = label or name
        arc_style = "->" if directed else "--"

        yield f'{"strict " if strict else ""}{"digraph" if directed else "graph"} "{label}" {{'
        yield ""

        for node in self.nodes.values():
            node_hash = hash(node)
            yield (
                f"{node_hash}"
                f' ['
                f' label="{node.label}", weight={node.weight:.02f}'
                f' color="#{node.stroke.r:02x}{node.stroke.g:02x}{node.stroke.b:02x}{node.stroke.a:02x}"'
                f' fontcolor="#{node.color.r:02x}{node.color.g:02x}{node.color.b:02x}{node.color.a:02x}"'
                f' fillcolor="#{node.fill.r:02x}{node.fill.g:02x}{node.fill.b:02x}{node.fill.a:02x}"'
                f' ]'
            )

            ranks = sorted({self.nodes[i].rank for i in self.children(node.name)})
            for child in [c for c in (self.nodes[i] for i in self.children(node.name)) if c.rank == ranks[0]]:
                child_hash = hash(child)
                yield (
                    f"{node_hash} {arc_style} {child_hash}"
                    f' ['
                    f' label="{self.args.label_inherits}", weight={node.weight:.02f}'
                    f' color="#{node.stroke.r:02x}{node.stroke.g:02x}{node.stroke.b:02x}{node.stroke.a:02x}"'
                    f' fontcolor="#{node.color.r:02x}{node.color.g:02x}{node.color.b:02x}{node.color.a:02x}"'
                    f' fillcolor="#{node.fill.r:02x}{node.fill.g:02x}{node.fill.b:02x}{node.fill.a:02x}"'
                    f' ]'
                )


            for arc in node.arcs:
                target_hash = hash(self.nodes[arc.target])
                yield (
                    f"{node_hash} {arc_style} {target_hash}"
                    f' ['
                    f' label="{arc.label}", weight={arc.weight:.02f}'
                    f' color="#{arc.stroke.r:02x}{arc.stroke.g:02x}{arc.stroke.b:02x}{arc.stroke.a:02x}"'
                    f' fontcolor="#{arc.color.r:02x}{arc.color.g:02x}{arc.color.b:02x}{arc.color.a:02x}"'
                    f' fillcolor="#{arc.fill.r:02x}{arc.fill.g:02x}{arc.fill.b:02x}{arc.fill.a:02x}"'
                    f' ]'
                )
            yield ""

        yield ""
        yield "}"


def load_rules(*paths: tuple[pathlib.Path]):
    for path in paths:
        text = path.read_text()
        print("Processed", pathlib.Path(path).resolve(), file=sys.stderr)
        yield from Stager.load(text)


def main(args):
    data = list(load_rules(*args.input))
    stager = Stager(rules=data)
    realms = {
        realm: list(sorter.static_order()) or [
            puzzle.get("name")
            for strand in stager.realms[realm].values()
            for puzzle in strand.get("puzzles", [])
            if puzzle.get("name")
        ]
        for realm, sorter in stager.strands.items()
    }
    puzzles = {
        (realm, name): stager.gather_puzzle(realm, name)
        for realm, names in realms.items()
        for name in names
    }
    pprint.pprint(puzzles)
    return 0

    if not args.input:
        print("No files processed.")
        return 2

    name = pathlib.Path(paths[0]).stem

    model = Model(parser.write_string(), parser.tables, args=args)
    if args.cluster:
        writer = model.to_cluster(name=name, label=args.label_graph, directed=args.digraph, strict=False)
    else:
        writer = model.to_dot(name=name, label=args.label_graph, directed=args.digraph, strict=False)

    lines = list(writer)
    print(*lines, sep="\n", file=sys.stdout)
    print("Generated", len(lines), "lines of output.", file=sys.stderr)


def parser():
    rv = argparse.ArgumentParser(__doc__)
    rv.add_argument(
        "--label-graph", default=None,
        help="Set a label for the graph."
    )
    rv.add_argument(
        "--label-inherits", default="...",
        help="Set the label for an arc signifying an 'inherits' relationship."
    )
    rv.add_argument(
        "--cluster", default=False, action="store_true",
        help="Generate a clustered graph."
    )
    rv.add_argument(
        "--digraph", "--directed", default=False, action="store_true",
        help="Make arcs directional."
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
