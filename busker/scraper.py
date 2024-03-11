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


import functools
import re

import xml.etree.ElementTree as ET

import httpx


class Tactic:

    def __call_(self):
        dara = {}
        response = httpx.post(url, data=data)
        return response


class Scraper:

    @staticmethod
    @functools.cache
    def tag_matcher(tag: str):
        return re.compile(f"<{tag}>.*?<\\/{tag}>", re.DOTALL)

    @staticmethod
    def find_forms(body: str):
        root = ET.fromstring(body)
        return root.findall("form")
