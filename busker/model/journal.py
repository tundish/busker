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

from collections import UserDict
from collections import UserList
from collections import UserString
from collections.abc import Mapping
from collections.abc import MutableSequence
from collections.abc import Sequence
from collections.abc import Set
import contextlib
import functools
import itertools
import logging
import pathlib

import jsonpath

from busker.model.types import Adaptor
from busker.model.types import Chain
from busker.model.types import Element
from busker.model.types import ElementType
from busker.model.types import Frame
from busker.model.types import Lens
from busker.model.types import Selector


class JournalEnvironment(jsonpath.JSONPathEnvironment):
    """
    Modifications to the python-jsonpath library.
    * allow attribute access semantics.
    * allow wildcards to apply to sets.

    """

    def _resolve_name(self, node):
        if self.token.kind == jsonpath.token.TOKEN_NAME and hasattr(node.obj, self.name):
            match = node.new_child(getattr(node.obj, self.name), self.name)
            node.add_child(match)
            yield match

        if isinstance(node.obj, Mapping):
            with contextlib.suppress(KeyError):
                match = node.new_child(self.env.getitem(node.obj, self.name), self.name)
                node.add_child(match)
                yield match

    def _resolve_wildcard(self, node):
        if isinstance(node.obj, Mapping):
            for key, val in node.obj.items():
                match = node.new_child(val, key)
                node.add_child(match)
                yield match

        elif isinstance(node.obj, (Set, Sequence)) and not isinstance(node.obj, str):
            for i, val in enumerate(node.obj):
                match = node.new_child(val, i)
                node.add_child(match)
                yield match


class Syntax(Lens):
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
        jsonpath.selectors.NameSelector.resolve = JournalEnvironment._resolve_name
        jsonpath.selectors.WildcardSelector.resolve = JournalEnvironment._resolve_wildcard
        self.env = JournalEnvironment()

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
        return functools.reduce(self.merge, chains)

    def search(self, query: str, data: dict, **kwargs) -> list:
        return self.env.findall(query, data, **kwargs)

    def actions(self, path: tuple) -> dict:
        levels = [path[0: n] for n in range(len(path) + 1)]
        frames = [self.doc.data.get(level, []) for level in levels]
        elements = [
            i for frame in frames for i in frame
            if isinstance(i, Element) and i.handler
        ]
        context = self.context(path)

        rv = dict()
        for element in elements:
            results = {
                k: self.search(v, context)
                for k, v in element.get("params", {}).items()
            }
            products = set(itertools.product(*results.values()))
            for term in element.get("terms", []):
                for product in products:
                    kwargs = dict(zip(element["params"], product))
                    phrase = term.format(**kwargs)
                    rv[phrase.lower()] = (element, kwargs)
        return rv


class Journal:

    def __init__(self, *args, uri: pathlib.Path | str = None):
        self.registry = {
            cls: [arg for arg in args if isinstance(arg, cls)]
            for cls in (Adaptor, Selector, Lens)
        }
        self.uri = uri
        self._scan = list()

    def attach(self, component: Adaptor | Selector | Lens):
        raise NotImplementedError

    def remove(self, component: Adaptor | Selector | Lens):
        raise NotImplementedError

    @property
    def adaptor(self):
        return next(
            (i for i in self.registry.get(Adaptor, []) if self.uri.suffix in i.backend.value),
            None
        )

    @property
    def marking(self):
        return [
            element for frame in self.adaptor.data.values()
            for element in frame
            if getattr(element, "type", None) == ElementType.MARKING.value
        ]

    @property
    def model(self):
        """
        Decorate each frame with its path, and each Element with its type.

        """
        logger = logging.getLogger(self.__class__.__name__.lower())
        data = self.adaptor.data
        for p in list(data):
            frame = data[p] = Frame(data[p].data)
            frame.path = p
            for n, obj in enumerate(frame.copy()):
                try:
                    frame[n] = Element(obj.data)
                except AttributeError:
                    logger.debug(f"Not a data element: {obj}")
                    continue
                except ValueError:
                    logger.debug(f"Not a data element: {obj}")
                    if isinstance(obj, UserString):
                        frame[n].type = ElementType.CONTENT
                    continue
                finally:
                    frame[n].parent = frame

                try:
                    frame[n].type = ElementType[obj["type"].upper()]
                except KeyError:
                    if "type" in obj:
                        logger.error(f"Unknown resource type: {obj['type']}")
                    else:
                        logger.error(f"Type value missing: path {p} item {n}")
                    return

            frame.refresh()
        return data
