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

    def __init__(self, url=None, method="post"):
        self.url=url

    def run(self, scraper: Scraper, prior: Node = None, **kwargs):
        reply = scraper.get_page(self.url, **kwargs)
        node=Node(
            datetime.datetime.now(datetime.timezone.utc),
            hashlib.blake2b(reply).hexdigest(),
            self.__class__.__name__,
            tuple(kwargs.items()),
            self.url,
        )
        return node, reply


class GetButtons(Tactic):
    pass


class PostSession(Tactic):
    pass


class GetOptions(Tactic):
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
            GetButtons(self.url),
            # PostSession(self.url),
            # GetOptions(self.url),
            # PostText(self.url),
        ])

    def __call__(self, tactic, *args, **kwargs):
        self.log(f"Tactic: '{tactic.__class__.__name__}'")

        node, doc = tactic.run(self.scraper, **kwargs)
        self.log(doc.decode("utf8"), level=logging.DEBUG)
        return node
