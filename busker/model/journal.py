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

from collections import defaultdict
from collections import UserString
from collections.abc import Mapping
import logging
import pathlib

from busker.model.types import Adaptor
from busker.model.types import Element
from busker.model.types import ElementType
from busker.model.types import Frame
from busker.model.types import Lens
from busker.model.types import Selector


class Journal:

    def __init__(self, *args, uri: pathlib.Path | str = None):
        """
        Lazy construction:
        1. __init__
        2. attach
        3. scan

        """
        self.uri = pathlib.Path(uri)
        self.registry = defaultdict(set)
        self.attach(*args)

    def __getattr__(self, name):
        try:
            return next(
                getattr(i, name)
                for typ in (Selector, Lens)
                for i in self.registry[typ]
                if hasattr(i, name)
            )
        except StopIteration:
            raise AttributeError(name)

    def register(self, helper):
        rv = None
        for cls in (Adaptor, Selector, Lens):
            if isinstance(helper, type) and issubclass(helper, cls):
                helper = helper(self)
            if isinstance(helper, cls):
                helper.journal = self
                self.registry[cls].add(helper)
                rv = helper
        return rv

    def attach(self, *helpers: Adaptor | Selector | Lens):
        for helper in helpers:
            self.register(helper)
        self.model  # Re-initialize model

    def remove(self, *helpers: Adaptor | Selector | Lens):
        for helper in helpers:
            for registered in self.registry.values():
                registered.discard(helper)
        self.model  # Re-initialize model

    @property
    def adaptor(self):
        return next(
            (i for i in self.registry.get(Adaptor, []) if self.uri.suffix in i.backend.value),
            None
        )

    @property
    def marking(self):
        return {
            getattr(element, "name", None): element
            for frame in self.adaptor.data.values()
            for element in frame
            if getattr(element, "type", None) == ElementType.MARKING.value
        }

    @property
    def model(self) -> Mapping:
        """
        Decorate each frame with its path, and each Element with its type.

        """
        logger = logging.getLogger(self.__class__.__name__.lower())
        try:
            data = self.adaptor.data
        except Exception as err:
            logger.warning(f"Journal can find no adaptor. Check {self.uri=}")
            logger.debug(err, exc_info=True)
            return {}

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

    def scan(self, **kwargs):
        adaptor = self.adaptor
        data = adaptor.load(self.uri)
        return list(adaptor.scan(data, **kwargs))
