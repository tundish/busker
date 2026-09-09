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
from fractions import Fraction
import logging
from numbers import Number

from busker.model.types import ElementType


@dataclasses.dataclass(kw_only=True)
class Marker:
    name: str
    view: tuple = None
    tick: int = 0
    face: tuple = (0, 1)
    span: Number = None
    type: str = ElementType.MARKING.value
    twist: bool = False
    memo: Counter = dataclasses.field(default_factory=Counter, compare=False)

    def __post_init__(self):
        try:
            self.view = tuple(self.view)
        except TypeError:
            self.view = tuple()
        self.type = ElementType.MARKING.value
        self.memo = Counter(self.memo)

    def jump(self, path: tuple, cost: Number=0, spin: tuple = None, **kwargs) -> dict:
        if cost > self.span:
            return {}
        if self.twist and spin is not None:
            face = Fraction(*self.face) + Fraction(*spin)
            return dict(view=path, tick=self.tick + 1, face=(face.numerator, face.denominator))
        else:
            return dict(view=path, tick=self.tick + 1, face=spin or self.face)

    def move(self, path: tuple, cost: Number=0, spin: tuple = None, **kwargs):
        jump = self.jump(path, cost=cost, spin=spin, **kwargs)
        for k, v in jump.items():
            setattr(self, k, v)
        self.memo[path] += 1
        return jump
