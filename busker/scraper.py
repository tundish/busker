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


from collections import namedtuple
import datetime
import hashlib
import functools
import re
import urllib.request
import xml.etree.ElementTree as ET

from busker.history import SharedHistory


Node = namedtuple(
    "Node", [
        "ts", "hash",
        "tactic", "params",
        "url",
        "title", "links", "blocks", "media",
        "options", "actions",
        "text"
    ],
    defaults=[
        None, None,
        None,
        None, None, None, None,
        None, None,
        None,
    ],
)


Form = namedtuple("Form", ["name", "action", "method", "inputs", "button"], defaults=[None])


Input = namedtuple(
    "Input", [
        "name",
        "type",
        "placeholder", "pattern",
        "autofocus", "required",
        "values",
        "title", "label",
    ],
    defaults = [None, None, None, None, None, None, None, None, None]
)


class LocalClient(urllib.request.OpenerDirector):

    def __init__(self, handlers: list=None):
        super().__init__()
        handlers = handlers or (
            urllib.request.UnknownHandler,
            urllib.request.HTTPDefaultErrorHandler,
            urllib.request.HTTPRedirectHandler,
            urllib.request.HTTPHandler,
            urllib.request.HTTPSHandler,
            urllib.request.HTTPErrorProcessor,
        )

        for handler_class in handlers:
            self.add_handler(handler_class())


class Scraper(SharedHistory):

    @staticmethod
    @functools.cache
    def tag_matcher(tag: str):
        return re.compile(f"(<{tag}.*?>)(.*?)(<\\/{tag}>)", re.DOTALL)

    @staticmethod
    def find_forms(body: str):
        root = ET.fromstring(body)
        return root.findall(".//form")

    @staticmethod
    def find_blocks(body: str):
        matcher = Scraper.tag_matcher("blockquote")
        return ["".join(i).strip() for i in matcher.findall(body, re.DOTALL)]

    @staticmethod
    def find_title(doc: str):
        matcher = Scraper.tag_matcher("title")
        match = matcher.search(doc)
        return match and match[2]

    def get_forms(self, body: str):
        root = ET.fromstring(body)
        for form_node in root.findall(".//form"):
            inputs = tuple(
                Input(**dict(
                    {k: v for k, v in node.attrib.items() if k in Input._fields},
                    values=tuple(filter(
                        None,
                        (i.attrib.get("value")
                        for i in root.find(".//datalist[@id='{0}']".format(node.attrib.get("list"))))
                    )),
                    label=getattr(root.find(".//label[@for='{0}']".format(node.attrib.get("name"))), "text", "")
                ))
                for node in form_node.findall(".//input")
            )
            yield Form(**dict(
                {k: v for k, v in form_node.attrib.items() if k in Form._fields},
                inputs=inputs,
                button=getattr(form_node.find(".//button[@type='submit']"), "text", None),
            ))

    def get(self, url=None, **kwargs) -> Node:
        self.log(f"GET {url=}")
        client = LocalClient()
        with client.open(url) as response:
            reply = response.read()

        return Node(
            ts=datetime.datetime.now(datetime.timezone.utc),
            hash=hashlib.blake2b(reply).hexdigest(),
            url=response.url,
            text = reply.decode("utf8"),
        )

    def post(self, url, data=None, **kwargs) -> Node:
        params = urllib.parse.urlencode(data).encode("utf8")
        self.log(f"POST {url=} {params=}")
        client = LocalClient()
        with client.open(url, params) as response:
            reply = response.read()

        return Node(
            ts=datetime.datetime.now(datetime.timezone.utc),
            hash=hashlib.blake2b(reply).hexdigest(),
            url=response.url,
            text = reply.decode("utf8"),
        )
