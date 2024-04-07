#!/usr/bin/env python3
#   encoding: utf-8

# This is part of the Busker library.
# Copyright (C) 2024 D E Haynes

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from collections import defaultdict
from collections import deque
from collections import namedtuple
import datetime
import functools
import itertools
import logging
import random
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from busker.history import SharedHistory
from busker.scraper import Scraper
from busker.scraper import Node
from busker.tactics import Read
from busker.tactics import Write
from busker.types import Choice


class Visitor(SharedHistory):

    def __init__(self, url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.scraper = Scraper()
        self.options = defaultdict(deque)
        self.records = defaultdict(deque)
        self.tactics = deque([Read(url=self.url)])

    @property
    def turns(self):
        return len([i for record in self.records.values() for i in record])

    def __call__(self, tactic, *args, **kwargs):

        self.log(f"Tactic: {tactic.__class__.__name__} {tactic.choice}")

        try:
            node = tactic.run(self.scraper, **kwargs)
        except urllib.error.HTTPError as e:
            value = f'{tactic.choice.value}' if tactic.choice.value is not None else "None"
            self.log(
                f"Stopped trying {tactic.__class__.__name__} of {value} to {tactic.url}",
                level=logging.WARNING
            )
            self.log(f"Caught error {e}", level=logging.WARNING)
            return

        if tactic.choice:
            self.records[node.hash].append(tactic.choice.value)

        options = [i for i in node.options if i not in self.options[node.hash]]
        self.log(f"New options: {options}", level=logging.DEBUG)
        self.options[node.hash].extend(options)

        if not node.actions:
            return node

        choice = Choice(form=random.randrange(len(node.actions)))
        try:
            # TODO: Better understanding of input fields
            choice = choice._replace(input=random.randrange(len(node.actions[choice.form].inputs)))
            choice = choice._replace(value=random.choice(node.actions[choice.form].inputs[choice.input].values))
        except ValueError:
            # No inputs in form
            pass

        # Back out of dead ends
        if self.records[node.hash] and set(self.records[node.hash]) >= set(self.options[node.hash]):
            choice = choice._replace(value=None)

        if node.url != self.url or len(self.records) == 1:
            self.tactics.append(Write(node, choice=choice))

        return node
