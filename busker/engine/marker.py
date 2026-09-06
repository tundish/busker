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

from collections import Counter
import dataclasses
import logging

from busker.model.types import ElementType

"""
def some_sync_generator(path):
    with open(path) as ...:
        yield ...

# DON'T do this
for obj in some_sync_generator(path):
    ...

# DO do this
from contextlib import closing
with closing(some_sync_generator(path)) as tmp:
    for obj in tmp:
"""


# Order of implementation
# Marker
# + visit counter for every path
#
# Content
# + style
# + theme
# + pulse - allow eg: (0, 1E99) for one-shots
#
# types text/speechmark or text/plain so factory param required

@dataclasses.dataclass(kw_only=True)
class Marker:
    name: str
    view: tuple = None
    tick: int = 0
    face: tuple = (0, 1)
    span: int = None
    type: str = ElementType.MARKING.value
    memo: Counter = dataclasses.field(default_factory=Counter, compare=False)

    def __post_init__(self):
        try:
            self.view = tuple(self.view)
        except TypeError:
            self.view = tuple()
        self.type = ElementType.MARKING.value


