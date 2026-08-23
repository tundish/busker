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

# Stage: Python code (world entity query model)
# Story: Speech      (scene drama directives model)

from collections.abc import Mapping
from collections.abc import MutableSequence
from collections.abc import Set
import contextlib
import itertools

import jsonpath

from busker.model.plotline import Plotline
from busker.model.types import Chain
from busker.model.types import ElementType


class MonkeyPatch:
    """
    Modifications to the python-jsonpath library to allow attribute access semantics.

    """

    def _resolve(self, node):
        if self.token.kind == jsonpath.token.TOKEN_NAME and hasattr(node.obj, self.name):
            match = node.new_child(getattr(node.obj, self.name), self.name)
            node.add_child(match)
            yield match

        if isinstance(node.obj, Mapping):
            with contextlib.suppress(KeyError):
                match = node.new_child(self.env.getitem(node.obj, self.name), self.name)
                node.add_child(match)
                yield match


class Journal(Plotline):
    """
    Access to Resource HyperTree (.rht) data.

    """

    @staticmethod
    def merge(body: dict, item: dict):
        """
        Merge a new item (by copy) into the context body.
        Chains are built from the leaf up toward the root.
        Consequently ordered sequences are built first in, last out.

        """
        stack = [(body.copy(), item.copy())]
        while stack:
            body, item = stack.pop(0)
            for k, v in item.items():
                if isinstance(v, Set):
                    try:
                        body[k] = body[k].union(v)
                    except AttributeError:
                        v = list(v)
                    except KeyError:
                        body[k] = v
                        continue

                if isinstance(v, MutableSequence):
                    try:
                        # FILO
                        body[k] = v.copy() + body[k]
                    except AttributeError:
                        v = tuple(v)
                    except KeyError:
                        body[k] = v
                        continue

                if k not in body:
                    body[k] = v
                elif isinstance(body[k], Mapping):
                    stack.append((body[k].copy(), v))
        return body

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        jsonpath.selectors.NameSelector.resolve = MonkeyPatch._resolve
        self.env = jsonpath.JSONPathEnvironment()

    @property
    def tree(self) -> dict:
        "Expand the document into a nested tree of frames"
        rv = dict()
        done = dict()
        paths = list(self.doc.data)
        for path in paths:
            node = rv
            for n, key in enumerate(path):
                pos = tuple(path[:n + 1])
                if pos in done:
                    node = done[pos]
                    continue

                try:
                    frame = self.doc.data[pos]
                    node[key] = Chain(*(i for i in frame if i.type == ElementType.CONTEXT.value))
                except KeyError:
                    node[key] = Chain()

                node[key] = node[key].new_child()
                done[pos] = node[key]
        return rv

    def context(self, path: tuple) -> Chain:
        "Build a view of the document as seen from the supplied path"
        levels = [path[0: n] for n in range(len(path) + 1)]
        frames = [self.doc.data.get(level, []) for level in levels]
        chains = [
            Chain(*(i for i in frame if getattr(i, "type", None) == ElementType.CONTEXT.value))
            for frame in reversed(frames)
        ]
        rv = list(itertools.accumulate(chains, self.merge))
        return rv[-1] if rv else {}

    def search(self, query: str, data: dict, **kwargs) -> list:
        return self.env.findall(query, data, **kwargs)

    def actions(self, path: tuple) -> dict:
        frames = self.doc.data.get(path, [])
        return frames
        chains = [
            Chain(*(i for i in frame if i.type == ElementType.CONTEXT.value))
            for frame in reversed(frames)
        ]
        return self.env.findall(query, data, **kwargs)
