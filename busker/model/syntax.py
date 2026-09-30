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
import logging

from busker.model.types import Chain
from busker.model.types import Element
from busker.model.types import ElementType
from busker.model.types import Lens


class Syntax(Lens):
    """
    Combinatorial synthesis of syntax

    """
    def __init__(self, journal: object):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.journal = journal

    def actions(self, path: tuple) -> dict:
        levels = [path[0: n] for n in range(len(path) + 1)]
        frames = [self.journal.adaptor.data.get(level, []) for level in levels]
        elements = [
            i for frame in frames for i in frame
            if isinstance(i, Element) and i.handler
        ]
        context = self.journal.context(path)

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
