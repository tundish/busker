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

import difflib
import logging
import sched
from busker.model.journal import Journal


class Engine:

    ignored_words = ("a", "an", "any", "her", "his", "my", "some", "the", "their")

    def __init__(self, rht: Journal = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.rht = rht
        self.clocks = dict(self.set_clocks(rht))

    @staticmethod
    def split_to_words(text: str, preserver=".", discard=None):
        discard = discard or set()
        return [
            i.strip()
            for i in text.rstrip(preserver).lower().split()
            if i not in discard or text.endswith(preserver)
        ]

    def match_text_to_phrases(self, text: str, phrases: list[str], precision=0.95):
        words = self.split_to_words(text, discard=self.ignored_words)
        print(f"{words=}")
        return difflib.get_close_matches(
            " ".join(words), phrases, cutoff=precision
        ) or difflib.get_close_matches(text.strip(), phrases, cutoff=precision)

    @staticmethod
    def set_clocks(rht):
        for marker in rht.marking:
            marker.scheduler = sched.scheduler()
            yield marker["name"], marker

    def cmd(self, text: str, marker: dict, precision=0.95, **kwargs):
        actions = self.rht.actions(marker.parent.path)
        matches = self.match_text_to_phrases(text, actions)

        self.logger.debug(f"{marker.parent.path=}")
        # Advance tick

    def put(self, *args, delay=0, **kwargs):
        return [
            marker.scheduler.enter(
                delay, n, self.cmd, argument=(arg, marker), kwargs=kwargs
            )
            for n, arg in enumerate(args)
            for marker in self.clocks.values()
        ]

    def step(self, **kwargs):
        import time
        for marker in self.clocks.values():
            delta = 0
            then = time.time()
            while delta is not None:
                time.sleep(delta)
                delta = marker.scheduler.run(blocking=False)
