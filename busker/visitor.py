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
        forms = body_match and tuple(scraper.get_forms(body_match[0]))

        return node._replace(
            tactic=self.__class__.__name__,
            params=tuple(kwargs.items()),
            title=title_match and title_match.group(),

            options=tuple(i.values for f in forms for i in f.inputs),
            actions=forms,
        )
        return node


class Write(Tactic):
    def run(self, scraper: Scraper, **kwargs) -> Node:
        form = self.prior.actions[self.choice.form]
        if form and form.method.lower() == "post":
            parts = urllib.parse.urlparse(form.action)
            if not parts.scheme:
                parts = urllib.parse.urlparse(f"{self.prior.url}{form.action}")
            url = urllib.parse.urlunparse(parts)

            if self.choice.input is None:
                data = dict()
            else:
                data = {form.inputs[self.choice.input].name: self.choice.value}
                print(f"{data=}")

            rv = scraper.post(url, data)

            body_re = scraper.tag_matcher("body")
            body_match = body_re.search(rv.text)

            title_match = scraper.find_title(rv.text)
            forms = body_match and tuple(scraper.get_forms(body_match[0]))

            rv = rv._replace(
                tactic=self.__class__.__name__,
                params=tuple(kwargs.items()),
                title=title_match and title_match.group(),

                options=tuple(itertools.chain(i.values for f in forms for i in f.inputs)),
                actions=forms,
            )
            return rv


class Visitor(SharedHistory):

    def __init__(self, url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.scraper = Scraper()
        self.record = defaultdict(deque)
        self.tactics = deque([
            Read(url=self.url),
        ])

    def __call__(self, tactic, *args, **kwargs):
        if any(tactic.choice or []):
            self.log(f"Tactic: {tactic.__class__.__name__} {tactic.choice}")
        else:
            self.log(f"Tactic: {tactic.__class__.__name__}")

        node = tactic.run(self.scraper, **kwargs)

        options = [i for i in node.options if i not in self.record[node.title]]
        self.log(f"New options: {options}", level=logging.DEBUG)
        self.record[node.title].extend(options)

        if not node.actions:
            return node

        # TODO: Back out of dead ends with empty body
        choice = Choice(form=random.randrange(len(node.actions)))
        try:
            choice = choice._replace(input=random.randrange(len(node.actions[choice.form].inputs)))
            choice = choice._replace(value=random.choice(node.actions[choice.form].inputs[choice.input].values))
        except ValueError:
            # No inputs to form
            pass
        finally:
            self.tactics.append(Write(node, choice=choice))

        return node
