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

"""

> The whole is other than the sum of its parts.
>
> -- <cite>Kurt Koffka</cite>

"""

from collections import defaultdict
from collections import UserString
from collections.abc import Mapping
import functools
import logging
import operator
import pathlib
import threading

from busker.model.types import Adaptor
from busker.model.types import Element
from busker.model.types import ElementType
from busker.model.types import Frame
from busker.model.types import Lens
from busker.model.types import Selector


class Journal:
    """
    A Journal is a composite object which provides read and write access to data.

    The main functionality of a Journal comes from the Lenses it uses.
    You can attach or remove them at run time. Any methods supplied by these objects
    can be called as if they were methods of the Journal.

    Journals are used as follows:

    1. Create a Journal object.
    2. Attach the lenses you want to apply to the document.
    3. Scan the document.

    """

    def __init__(self, *args, uri: pathlib.Path | str = None):
        """

        `*args`
        :   `busker.model.types.Lens` subclasses or instantiated objects of such types.

        `uri`
        : A path-like object to a document file.

        """
        self._logger = logging.getLogger(self.__class__.__name__.lower())
        self.uri = pathlib.Path(uri)
        """The uri of the current document."""
        self.write_lock = threading.RLock()
        """A re-entrant lock to protect write access to data."""
        self.registry: dict = defaultdict(set)
        """A registry of Lenses."""
        self.attach(*args)

    def __getattr__(self, name):
        return self.lookup_lens(name)

    @functools.lru_cache
    def lookup_lens(self, name: str) -> Lens:
        """
        Identify a lens from the registry.

        `name`
        : The name of a method supplied by the lens

        """
        try:
            return next(getattr(i, name) for i in self.registry[Lens] if hasattr(i, name))
        except StopIteration:
            raise AttributeError(name)

    def _register(self, helper: Adaptor | Lens):
        """
        Register a helper lens or adaptor for use in the Journal.

        `helper`
        :   An adaptor or lens object

        """
        rv = None
        for cls in (Adaptor, Lens):
            if isinstance(helper, type) and issubclass(helper, cls):
                helper = helper(self)
            if isinstance(helper, cls):
                helper.journal = self
                self.registry[cls].add(helper)
                rv = helper
        return rv

    def attach(self, *helpers: Adaptor | Lens):
        """
        Attach a helper lens or adaptor to the Journal.

        `helpers`
        :   Objects or classes

        """
        with self.write_lock:
            for helper in helpers:
                self._register(helper)
            self.lookup_lens.cache_clear()
        _ = self.model  # Re-initialize model

    def remove(self, *helpers: Adaptor | Lens):
        """
        Remove a helper lens or adaptor from the Journal.

        `helpers`
        :   Objects or classes

        """
        with self.write_lock:
            for helper in helpers:
                for registered in self.registry.values():
                    if isinstance(helper, type):
                        try:
                            types = {type(i): i for i in registered}
                            helper = types[helper]
                        except KeyError:
                            continue
                    registered.discard(helper)
                    helper.journal = None
            self.lookup_lens.cache_clear()
        _ = self.model  # Re-initialize model

    @property
    def adaptor(self) -> Adaptor:
        """The current adaptor for the backend data."""
        return next(
            (i for i in self.registry.get(Adaptor, []) if self.uri.suffix in i.backend.value),
            None
        )

    @property
    def marking(self) -> dict:
        """A dictionary of all markers. Stored by name."""
        store = defaultdict(list)
        for frame in self.adaptor.data.values():
            for element in frame:
                if getattr(element, "type", None) == ElementType.MARKING.value:
                    store[element.rank].append(element)

        # Reverse iterate so that duplicate names get picked according to rank
        picks = dict(
            (v.name, v)
            for k in reversed(sorted(store))
            for v in reversed(sorted(store[k], key=lambda m: m.name))
        )
        return dict(reversed(picks.items()))

    @property
    def model(self) -> Mapping:
        """
        A nested dictionary of objects. This is the internal model of the Journal.
        The original backend data is enriched with derived attributes.
        Each frame with its path, and each Element with its type.

        """
        try:
            data = self.adaptor.data
        except Exception as err:
            self._logger.warning(f"Journal can find no adaptor. Check {self.uri=}")
            self._logger.debug(err, exc_info=True)
            return {}

        with self.write_lock:
            for p in list(data):
                frame = data[p] = Frame(data[p].data)
                frame.path = p
                for n, obj in enumerate(frame.copy()):
                    try:
                        frame[n] = Element(obj.data)
                    except AttributeError:
                        self._logger.debug(f"Not a data element: {obj}")
                        continue
                    except ValueError:
                        self._logger.debug(f"Not a data element: {obj}")
                        if isinstance(obj, UserString):
                            frame[n].type = ElementType.CONTENT
                        continue
                    finally:
                        frame[n].parent = frame
                        frame[n].index = n

                    try:
                        frame[n].type = ElementType[obj["type"].upper()]
                    except KeyError:
                        if "type" in obj:
                            self._logger.error(f"Unknown resource type: {obj['type']}")
                        else:
                            self._logger.error(f"Type value missing: path {p} item {n}")
                        return

                frame.refresh()
        return data

    def scan(self, **kwargs) -> list:
        """Read the backend data, and scan it into the internal model."""
        with self.write_lock:
            adaptor = self.adaptor
            data = adaptor.load(self.uri)
            rv = list(adaptor.scan(data, **kwargs))
            _ = self.model  # Re-initialize model
            return rv
