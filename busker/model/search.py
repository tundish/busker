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
from collections.abc import Set
from collections.abc import Sequence
import contextlib

from busker.model.types import Selector

import jsonpath
from jsonpath.function_extensions import ExpressionType
from jsonpath.function_extensions import FilterFunction


class StrFilterFunction(FilterFunction):
    """A JSONPath function extension returning the string representation of an object."""

    arg_types = [ExpressionType.VALUE]
    return_type = ExpressionType.VALUE

    def __call__(self, value: object) -> object:
        try:
            return str(value)
        except TypeError:
            return jsonpath.UNDEFINED


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

    def compare(self, left: object, operator: str, right: object) -> bool:
        if operator == "in" and isinstance(right, (Mapping, Set, Sequence)):
            return left in right
        if operator == "contains" and isinstance(left, (Mapping, Set, Sequence)):
            return right in left
        return super().compare(left, operator, right)


class Search(Selector):

    def __init__(self, journal: object):
        self.journal = journal
        jsonpath.selectors.NameSelector.resolve = JournalEnvironment._resolve_name
        jsonpath.selectors.WildcardSelector.resolve = JournalEnvironment._resolve_wildcard
        self.env = JournalEnvironment()
        self.env.function_extensions["str"] = StrFilterFunction()  # Experimental

    def search(self, query: str, data: dict, **kwargs) -> list:
        return self.env.findall(query, data, **kwargs)
