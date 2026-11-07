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

import ast
from collections import defaultdict
from collections import ChainMap
from collections import UserDict
from collections import UserList
import dataclasses
import enum
import textwrap
import typing
import warnings


class BackendType(enum.Enum):
    SQL3_DB = [".db"]
    RHT_TXT = [".rht"]


class ElementType(enum.StrEnum):
    COMMENT = enum.auto()
    CONTENT = enum.auto()
    CONTEXT = enum.auto()
    FIXTURE = enum.auto()
    HANDLER = enum.auto()
    HISTORY = enum.auto()
    LINKAGE = enum.auto()
    MARKING = enum.auto()
    MONITOR = enum.auto()
    TRIGGER = enum.auto()


class Rank(enum.IntEnum):
    READBACK =  2
    ELLIPSIS =  4
    PROLOGUE =  6
    LIBRETTO =  8
    DIALOGUE = 10
    EPILOGUE = 12
    ANALYSIS = 14
    GLOSSARY = 16


class Adaptor:
    """Parent class for objects which provide access to persistent data."""

    def scan(self, text: str):
        """
        `text`
        : The text of the document.

        Override this method in a subclass.

        """
        raise NotImplementedError


class Lens:
    """Parent class for objects which incorporate functionality into a `busker.model.journal.Journal`."""
    pass


class Selector(Lens):
    """Parent class for objects which allow search of data via a `busker.model.journal.Journal`."""

    def search(self, query: str, data: dict, **kwargs) -> list:
        """
        `query`
        : The query pattern for the search.

        `data`
        : The data to be searched.

        Override this method in a subclass.

        """
        raise NotImplementedError


Accumulator = lambda: defaultdict(complex)
"""A class to store counts using complex numbers."""


class Chain(ChainMap):
    """Variant of `collections.ChainMap` that allows direct updates to inner scopes."""

    def __setitem__(self, key, value):
        for mapping in self.maps:
            if key in mapping:
                mapping[key] = value
                return
        self.maps[0][key] = value

    def __delitem__(self, key):
        for mapping in self.maps:
            if key in mapping:
                del mapping[key]
                return
        raise KeyError(key)


class Frame(UserList):
    """A list which accepts custom attributes."""

    def refresh(self):
        """A signal to referenced objects that the container has changed."""
        for obj in self.data:
            try:
                obj.refresh(parent=self)
            except AttributeError:
                pass
        return self


class Element(UserDict):
    """A dictionary which accepts custom attributes."""

    @property
    def content(self):
        raise NotImplementedError

    @property
    def handler(self):
        """Return any handler associated with this element."""
        rv = None
        if self.data.get("type") != ElementType.HANDLER.value:
            return

        try:
            pos = self.parent.index(self)
        except ValueError:
            return

        try:
            rv = self.parent[pos + 1]
        except IndexError:
            warnings.warn(f"Expecting element at path {self.parent.path} after pos: {pos}")
            return

        if not isinstance(rv, ast.AST):
            warnings.warn(f"Expecting code at path {self.parent.path} after pos: {pos}")
            return

        self.rank = self.data.get("rank", Rank.ELLIPSIS)
        return rv

    @property
    def monitor(self):
        """Return any monitor associated with this element."""
        rv = None
        if self.data.get("type") != ElementType.MONITOR.value:
            return

        try:
            pos = self.parent.index(self)
        except ValueError:
            return

        try:
            rv = self.parent[pos + 1]
        except IndexError:
            warnings.warn(f"Expecting element at path {self.parent.path} after pos: {pos}")
            return

        if not isinstance(rv, ast.AST):
            warnings.warn(f"Expecting code at path {self.parent.path} after pos: {pos}")
            return

        self.rank = self.data.get("rank", Rank.ELLIPSIS)
        return rv

    def refresh(self, parent=None):
        """A signal to referenced objects that the container has changed."""
        self.parent = parent
        return self


@dataclasses.dataclass(order=True)
class Note:
    """A lightweight object which contains text yet to be ordered alongside others."""
    text: str = dataclasses.field(compare=False)
    """A text string"""
    rank: int = Rank.DIALOGUE
    """The declared rank of the text."""
    clip: int = 0
    """A secondary index for stable ordering."""

    def __post_init__(self):
        self.text = textwrap.dedent(self.text).lstrip()


class Exclamation(Exception):
    """A class for text-like Exceptions."""
    pass
