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

from collections import Counter
from collections import defaultdict
from collections import deque
import html
import html.parser
import logging
import random
import string
import urllib.error

from busker.history import SharedHistory
from busker.scraper import Node
from busker.scraper import Scraper
from busker.actions import Read
from busker.actions import Action
from busker.actions import Write
from busker.types import Choice


class Witness(html.parser.HTMLParser):

    def __init__(self, convert_charrefs=True):
        self.options = defaultdict(deque)
        self.commands = defaultdict(deque)
        self.words = Counter()
        self.animations = Counter()
        self.delays = []
        self.duration = 0
        super().__init__(convert_charrefs=convert_charrefs)

    def handle_starttag(self, tag, attrs):
        attribs = dict(attrs)
        try:
            styles = {
                k: v
                for k, _, v in [
                    i.partition(":")
                    for i in html.unescape(attribs["style"]).replace(" ", "").split(";")
                ] if _
            }
            if animation := styles.get("animation-duration"):
                self.animations[animation] += 1
            if delay := styles.get("animation-delay"):
                self.delays.append(float(delay.rstrip("s")))
        except KeyError:
            pass

    def handle_data(self, data):
        self.words.update([
            word
            for i in data.split(" ")
            if (word := i.strip(string.whitespace + string.punctuation).lower())
        ])

    def reset(self):
        super().reset()
        for variable in (self.words, self.animations, self.delays):
            variable.clear()
        self.duration = 0

    def untested(self, node: Node):
        return set(self.commands.get(node.hash, [])) - set(self.options.get(node.hash, []))

    def update(self, node: Node, choice: Choice):
        if choice:
            self.commands[node.hash].append(choice.value)

        options = [i for i in node.options if i not in self.options[node.hash]]
        self.options[node.hash].extend(options)
        for block in node.blocks:
            self.feed(block)

        if self.delays:
            self.duration += max(self.delays)
        self.delays.clear()


class Visitor(SharedHistory):

    def __init__(self, url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.scraper = Scraper()
        self.witness = Witness()
        self.actions = deque([Read(url=self.url)])

    @property
    def turns(self):
        return len([i for record in self.witness.commands.values() for i in record])

    def choose(self, node: Node) -> Choice:
        forms = {i.name: i for i in node.forms}
        rv = Choice(form=random.choice(list(forms)))
        try:
            inputs = {i.name: i for i in forms[rv.form].inputs}
            rv = rv._replace(input=random.choice(list(inputs)))
            rv = rv._replace(value=random.choice(inputs[rv.input].values))
        except IndexError:
            # No values to choose
            pass
        except ValueError:
            # No inputs in chosen form
            pass

        # Back out of dead ends
        if self.witness.commands[node.hash] and not self.witness.untested(node):
            rv = rv._replace(value=None)
        return rv

    def __call__(self, action, *args, **kwargs):

        self.log(f"Action: {action.__class__.__name__} {action.choice}")

        try:
            node = action.run(self.scraper, **kwargs)
            self.witness.update(node, action.choice)
            choice = self.choose(node)
        except urllib.error.HTTPError as e:
            self.log(
                f"Stopped trying {action.__class__.__name__} of {action.choice.value} to {action.url}",
                level=logging.WARNING
            )
            self.log(f"Caught error {e}", level=logging.WARNING)
            return

        self.actions.append(Write(node, choice=choice))

        return node
