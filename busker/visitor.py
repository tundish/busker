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

from collections import deque
from collections import namedtuple
import datetime
import functools
import itertools
import logging
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from busker.history import SharedHistory
from busker.scraper import Scraper
from busker.scraper import Node


class Tactic:

    @classmethod
    def registry(cls):
        return cls.__subclasses__()

    def __init__(self, node=None, url=None):
        self.node = node
        self.url = url

    def run(self, scraper: Scraper, prior: Node = None, **kwargs):
        url = self.node.url if self.node else self.url
        node = scraper.get(url, **kwargs)

        body_re = scraper.tag_matcher("body")
        body_match = body_re.search(node.text)

        title_match = scraper.find_title(node.text)
        forms = body_match and tuple(scraper.get_forms(body_match[0]))

        return node._replace(
            tactic=self.__class__.__name__,
            params=tuple(kwargs.items()),
            title=title_match and title_match.group(),

            options=tuple(itertools.chain(i.values for f in forms for i in f.inputs)),
            actions=forms,
        )
        return node


class PostSession(Tactic):
    def run(self, scraper: Scraper, prior: Node = None, **kwargs):
        node = super().run(scraper, prior, **kwargs)
        form = next(iter(node.actions), None)
        if form and form.method.lower() == "post":
            parts = urllib.parse.urlparse(form.action)
            if not parts.scheme:
                parts = urllib.parse.urlparse(f"{node.url}{form.action}")
            url = urllib.parse.urlunparse(parts)
            data = dict({}, **kwargs)

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


class PostText(Tactic):
    pass


class Visitor(SharedHistory):

    def __init__(self, url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.scraper = Scraper()
        self.ledger = {}
        self.tactics = deque([
            Tactic(url=self.url),
        ])

    def __call__(self, tactic, *args, **kwargs):
        self.log(f"Tactic: '{tactic.__class__.__name__}'")

        node = tactic.run(self.scraper, **kwargs)
        self.log(node.text, level=logging.DEBUG)
        if len(node.actions) == 0:
            pass
        if len(node.actions) == 1:
            if not node.actions[0].inputs:
                self.tactics.append(PostSession(node))
            else:
                self.tactics.append(PostText(node))
        return node
