#!/usr/bin/env python
#   encoding: utf-8

# Copyright (C) 2025 D E Haynes
# This file is part of spiki.

# Spiki is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# Spiki is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with spiki.
# If not, see <https://www.gnu.org/licenses/>.

from collections.abc import Generator
from collections import defaultdict
import io
import json
import logging
import mimetypes
import re

from spiki import __version__


class Multipart:

    def __init__(self, *args, path: list = None):
        self.logger = logging.getLogger("spiki.multipart")
        self.mark_regex = re.compile(r"^\{.+?\}$", re.MULTILINE)
        self.path = path
        self.data = defaultdict(list)
        for arg in args:
            self.data[path].append(arg)

    @property
    def header(self):
        if self.path is None:
            return dict(mark=id(self), spiki=__version__)
        else:
            return dict(mark=id(self), spiki=__version__, path=self.path[:])

    def __str__(self):
        return "\n".join((
            "{0}\n{1}".format(
                json.dumps(
                    dict(
                        self.header,
                        type="application/json"
                        if isinstance(i, (dict, list))
                        else "text/plain"
                    ),
                    sort_keys=False
                ),
                json.dumps(i, indent=0, sort_keys=False)
                if isinstance(i, (dict, list))
                else i
            )
            for n, (k, v) in enumerate(self.data.items())
            for i in v
        ))

    def feed(self, text: str, header_length=84, data_types=("application/json", )) -> Generator[dict]:
        delimiters = list(self.mark_regex.finditer(text))
        if not delimiters:
            self.logger.error("No delimiters found")
            return
        if (pos := delimiters[0].start()) != 0:
            self.logger.error(f"Header does not lead. Pos: {pos}")
            return

        try:
            header = json.loads(delimiters[0][0])
        except json.JSONDecodeError:
            self.logger.error(f"Invalid Header. Pos: {pos}")
            return

        mark = header.get("mark")
        if not mark:
            self.logger.error(f"No mark found. Pos: {pos}")
            return

        for n, d in enumerate(delimiters):
            if (pos := d.end()) - d.start() > header_length:
                self.logger.error(f"Delimiter too long. Pos: {pos}")
                return

            try:
                data = json.loads(d[0])
            except json.JSONDecodeError:
                self.logger.error(f"Invalid Delimiter. Pos: {pos}")
                return

            if data.get("mark") != mark:
                self.logger.error(f"Mark mismatch. Pos: {pos}")
                return

            if len(delimiters) - n > 1:
                data["payload"] = payload = text[d.end(): delimiters[n + 1].start()]
            else:
                data["payload"] = payload = text[d.end():]

            if data.get("type") in data_types:
                try:
                    data["payload"] = payload = json.loads(payload)
                except json.JSONDecodeError:
                    self.logger.error(f"Invalid Data. Pos: {d.end()}")
                    return

            path = data.get("path")
            self.data[path].append(payload)
            yield data
