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


Choice = namedtuple("Choice", ["form", "input", "value"], defaults=[None, None])


class Tactic:

    @classmethod
    def registry(cls):
        return cls.__subclasses__()

    def __init__(self, prior=None, url=None, choice: Choice = None):
        self.prior = prior
        self.url = url
        self.choice = choice

    def run(self, scraper: Scraper, **kwargs) -> Node:
        return Node(None, None)


class Read(Tactic):
    def run(self, scraper: Scraper, **kwargs) -> Node:
        url = self.prior.url if self.prior else self.url
        node = scraper.get(url, **kwargs)

        body_re = scraper.tag_matcher("body")
        body_match = body_re.search(node.text)

        title_match = scraper.find_title(node.text)
        forms = body_match and tuple(scraper.get_forms(body_match[0])) or tuple()
        blocks = body_match and tuple(scraper.find_blocks(body_match[0])) or tuple()

        return node._replace(
            tactic=self.__class__.__name__,
            params=tuple(kwargs.items()),
            title=title_match and title_match.group(),
            blocks=blocks,
            options=tuple(v for f in forms for i in f.inputs for v in i.values),
            actions=forms,
        )
        return node


class Write(Tactic):
    def run(self, scraper: Scraper, **kwargs) -> Node:
        form = {i.name: i for i in self.prior.actions}.get(self.choice.form, next(iter(self.prior.actions)))
        if form and form.method.lower() == "post":
            parts = urllib.parse.urlparse(form.action)
            if not parts.scheme:
                parts = urllib.parse.urlparse(f"{self.prior.url}{form.action}")
            self.url = urllib.parse.urlunparse(parts)

            if self.choice.input is None:
                data = dict()
            else:
                input_ = {i.name: i for i in form.inputs}.get(self.choice.input, next(iter(form.inputs)))
                data = {input_.name: self.choice.value}

            rv = scraper.post(self.url, data)

            body_re = scraper.tag_matcher("body")
            body_match = body_re.search(rv.text)

            forms = body_match and tuple(scraper.get_forms(body_match[0])) or tuple()
            blocks = body_match and tuple(scraper.find_blocks(body_match[0])) or tuple()

            rv = rv._replace(
                tactic=self.__class__.__name__,
                params=tuple(kwargs.items()),
                title = scraper.find_title(rv.text),
                blocks=blocks,
                options=tuple(v for f in forms for i in f.inputs for v in i.values),
                actions=forms,
            )
            return rv


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
