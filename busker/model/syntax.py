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

from collections.abc import Mapping
from collections.abc import MutableSequence
from collections.abc import Set
import functools
import itertools

from busker.model.types import Chain
from busker.model.types import Element
from busker.model.types import ElementType
from busker.model.types import Lens


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

    def __init__(self, journal: object):
        self.journal = journal

    def context(self, path: tuple) -> Chain:
        "Build a view of the document as seen from the supplied path"
        levels = [path[0: n] for n in range(len(path) + 1)]
        frames = [self.journal.adaptor.data.get(level, []) for level in levels]
        chains = [
            Chain(*(i for i in frame if getattr(i, "type", None) == ElementType.CONTEXT.value))
            for frame in reversed(frames)
        ]
        return functools.reduce(self.merge, chains)

    def actions(self, path: tuple) -> dict:
        levels = [path[0: n] for n in range(len(path) + 1)]
        frames = [self.journal.adaptor.data.get(level, []) for level in levels]
        elements = [
            i for frame in frames for i in frame
            if isinstance(i, Element) and i.handler
        ]
        context = self.context(path)

        rv = dict()
        for element in elements:
            results = {
                k: self.journal.search(v, context)
                for k, v in element.get("params", {}).items()
            }
            products = set(itertools.product(*results.values()))
            for term in element.get("terms", []):
                for product in products:
                    kwargs = dict(zip(element["params"], product))
                    phrase = term.format(**kwargs)
                    rv[phrase.lower()] = (element, kwargs)
        return rv
