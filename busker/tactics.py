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

import urllib.parse

from busker.scraper import Scraper
from busker.scraper import Node
from busker.types import Choice


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
