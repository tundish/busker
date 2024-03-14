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
import functools
import re
import urllib.request
import xml.etree.ElementTree as ET

from busker.history import SharedHistory


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


class Scraper(SharedHistory):

    @staticmethod
    @functools.cache
    def tag_matcher(tag: str):
        return re.compile(f"<{tag}>.*?<\\/{tag}>", re.DOTALL)

    @staticmethod
    def find_forms(body: str):
        root = ET.fromstring(body)
        return root.findall(".//form")

    @staticmethod
    def find_title(doc: str):
        matcher = Scraper.tag_matcher("title")
        return matcher.search(doc)

    def get_page(self, url=None):
        self.log(f"GET {url=}")
        with urllib.request.urlopen(url) as response:
            page = response.read()
        return page

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

    def post(self, url, data=None):
        params = urllib.parse.urlencode(data).encode("utf8")
        self.log(f"POST {url=} {params=}")
        with urllib.request.urlopen(url, params) as response:
            reply = response.read()
            print(f"{reply=}")
            return response

