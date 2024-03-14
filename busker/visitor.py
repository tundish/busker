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
import hashlib
import re
import urllib.request
import xml.etree.ElementTree as ET

from busker.history import SharedHistory
from busker.scraper import Scraper


Node = namedtuple(
    "Node", ["ts", "hash", "tactic", "params", "uri", "title", "links", "blocks", "media", "options", "actions"],
    defaults=[None, None, None, None, None, None],
)


class Tactic:

    @classmethod
    def registry(cls):
        return cls.__subclasses__()

    def __init__(self, node=None, url=None):
        self.node = node
        self.url = url

    def run(self, scraper: Scraper, prior: Node = None, **kwargs):
        url = self.node.uri if self.node else self.url
        reply = scraper.get_page(url, **kwargs)
        text = reply.decode("utf8")

        body_re = scraper.tag_matcher("body")
        body_match = body_re.search(text)

        title_match = scraper.find_title(text)
        forms = body_match and tuple(scraper.get_forms(body_match[0]))

        node=Node(
            datetime.datetime.now(datetime.timezone.utc),
            hashlib.blake2b(reply).hexdigest(),
            self.__class__.__name__,
            tuple(kwargs.items()),
            url,
            title=title_match and title_match.group(),

            options=tuple(itertools.chain(i.values for f in forms for i in f.inputs)),
            actions=forms,
        )
        return node, reply


class PostSession(Tactic):
    pass


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

        node, doc = tactic.run(self.scraper, **kwargs)
        self.log(doc.decode("utf8"), level=logging.DEBUG)
        if len(node.actions) == 0:
            pass
        if len(node.actions) == 1:
            if not node.actions[0].inputs:
                self.tactics.append(PostSession(node))
            else:
                self.tactics.append(PostText(node))
        return node
