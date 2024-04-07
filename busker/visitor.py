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
import html.parser
import logging
import random
import urllib.error

from busker.history import SharedHistory
from busker.scraper import Node
from busker.scraper import Scraper
from busker.tactics import Read
from busker.tactics import Tactic
from busker.tactics import Write
from busker.types import Choice


class Witness(html.parser.HTMLParser):

    def __init__(self, convert_charrefs=True):
        super().__init__(convert_charrefs=convert_charrefs)
        self.options = defaultdict(deque)
        self.commands = defaultdict(deque)

    def untested(self, node: Node):
        return set(self.commands.get(node.hash, [])) - set(self.options.get(node.hash, []))

    def update(self, node: Node, choice: Choice):
        if choice:
            self.commands[node.hash].append(choice.value)

        options = [i for i in node.options if i not in self.options[node.hash]]
        self.options[node.hash].extend(options)


class Visitor(SharedHistory):

    def __init__(self, url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.scraper = Scraper()
        self.witness = Witness()
        self.tactics = deque([Read(url=self.url)])

    @property
    def turns(self):
        return len([i for record in self.witness.commands.values() for i in record])

    def choose(self, node: Node) -> Choice:
        rv = Choice(form=random.randrange(len(node.actions)))
        try:
            rv = rv._replace(input=random.randrange(len(node.actions[rv.form].inputs)))
            rv = rv._replace(value=random.choice(node.actions[rv.form].inputs[rv.input].values))
        except ValueError:
            # No inputs in chosen form
            pass

        # Back out of dead ends
        if self.witness.commands[node.hash] and not self.witness.untested(node):
            rv = rv._replace(value=None)
        return rv

    def __call__(self, tactic, *args, **kwargs):

        self.log(f"Tactic: {tactic.__class__.__name__} {tactic.choice}")

        try:
            node = tactic.run(self.scraper, **kwargs)
            self.witness.update(node, tactic.choice)
            choice = self.choose(node)
        except urllib.error.HTTPError as e:
            value = f'{tactic.choice.value}' if tactic.choice.value is not None else "None"
            self.log(
                f"Stopped trying {tactic.__class__.__name__} of {value} to {tactic.url}",
                level=logging.WARNING
            )
            self.log(f"Caught error {e}", level=logging.WARNING)
            return

        if node.url != self.url or len(self.witness.commands) == 1:
            self.tactics.append(Write(node, choice=choice))

        return node
