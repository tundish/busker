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

import itertools
import logging
import operator

from spiki.conditions import Conditions

from busker.model.types import Accumulator


class Presenter(Conditions):

    def split_cues(self, text: str):
        self.processor.reset()
        self.processor.source.extend(text.splitlines(keepends=False))
        lines = list(itertools.islice(self.processor.source, self.processor._index, None))
        cues = dict(
            filter(
                operator.itemgetter(1),
                ((n, self.processor.cue_matcher.match(line)) for n, line in enumerate(lines)),
            )
        )
        blocks = list(
            itertools.pairwise(
                sorted(set(cues.keys()).union({0, len(lines)}))
            )
        )
        return ["\n".join(lines[begin:end]).rstrip() for begin, end in blocks]

    def rotate_cue(self, text: str, marker=None):
        html5 = self.processor.loads(text)
        if not self.processor.cues:
            return text
        cue = self.processor.cues[0]
        if "!" not in cue["fragments"]:
            return text
        if not cue["lines"]:
            return text
        index = marker.memo[marker.mark]
        n = int(index.imag) % len(cue["items"])
        rv = "\n".join((cue["lines"][0].replace("!", str(n)), cue["items"][n]))
        marker.memo[marker.mark] = index + 1j
        return rv
