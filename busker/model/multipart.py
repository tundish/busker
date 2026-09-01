#!/usr/bin/env python
#   encoding: utf-8

# Copyright (C) 2026 D E Haynes
# This file is part of busker.

# Busker is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# Busker is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with busker.
# If not, see <https://www.gnu.org/licenses/>.

import ast
from collections.abc import Generator
from collections.abc import MutableMapping
from collections import defaultdict
from collections import UserDict
from collections import UserList
from collections import UserString
import io
import json
import logging
import mimetypes
import pprint
import re

from busker import __version__


class Multipart:

    def __init__(
        self, *args,
        text: str = None,
        path: tuple = None,
        factory: dict= None,
    ):
        self.logger = logging.getLogger("busker.multipart")
        self.mark_regex = re.compile(r"^\{.+?\}$", re.MULTILINE)
        self.seal = id(self)
        self.path = path or tuple()

        self.factory = {dict: dict, list: list, str: str}
        self.factory.update(factory or {})

        self.data = defaultdict(self.factory[list])
        self.data[self.path].extend(args)

        if text is not None:
            list(self.feed(text))

    @property
    def header(self):
        if self.path is None:
            return dict(seal=self.seal, type=None, busker=__version__)
        else:
            return dict(seal=self.seal, type=None, busker=__version__, path=self.path[:])

    def __str__(self):
        return "\n".join(str(i) if isinstance(i, UserString) else i for i in self.dump())

    def feed(
        self, text: str, header_length=255,
        code_types=set(("application/x-python-code", "application/x-python", "application/python", "code/python")),
        data_types=set(("application/json", "text/json", "data/json", "text/python", "text/x-python", "data/python"))
    ) -> Generator[dict]:
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

        seal = header.get("seal")
        if seal:
            self.seal = seal
        else:
            self.logger.error(f"No seal found. Pos: {pos}")
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

            if data.get("seal") != seal:
                self.logger.error(f"Seal mismatch. Pos: {pos}")
                return

            if len(delimiters) - n > 1:
                data["payload"] = payload = text[d.end(): delimiters[n + 1].start()]
            else:
                data["payload"] = payload = text[d.end():]

            if data.get("type") in code_types:
                try:
                    path = format(data.get("path", self.path))
                except ValueError as err:
                    self.logger.error(f"Invalid Path. Pos: {d.end()}", exc_info=True)
                    return

                try:
                    data["payload"] = payload = ast.parse(payload, filename=path, mode="exec")
                except SyntaxError as err:
                    self.logger.error(f"Invalid Code. Pos: {d.end()}", exc_info=True)
                    return

            elif data.get("type") in data_types:
                parser = ast.literal_eval if "python" in data["type"] else json.loads
                try:
                    payload = parser(payload)
                    if type(payload) in self.factory:
                        payload = self.factory[type(payload)](payload)
                    data["payload"] = payload
                except (SyntaxError, ValueError) as err:
                    self.logger.error(f"Invalid Literal. Pos: {d.end()}", exc_info=True)
                    return
                except json.JSONDecodeError:
                    self.logger.error(f"Invalid Data. Pos: {d.end()}", exc_info=True)
                    return

            elif type(payload) in self.factory:
                data["payload"] = payload = self.factory[type(payload)](payload)

            path = tuple(data.get("path", self.path))
            self.data[path].append(payload)
            yield data

    def dump(self, safe=False):
        header = self.header
        for n, (k, v) in enumerate(self.data.items()):
            if n == 1: header.pop("busker", None)
            for i in v:
                if isinstance(i, ast.AST):
                    yield json.dumps(dict(header, type="code/python", path=k), sort_keys=False)
                    yield ast.unparse(i)
                elif isinstance(i, (dict, list, UserDict, UserList)):
                    yield json.dumps(dict(header, type="data/python", path=k), sort_keys=False)
                    if safe:
                        yield pprint.saferepr(i)
                    else:
                        yield pprint.pformat(i, compact=False, indent=1, sort_dicts=False, width=120)
                else:
                    yield json.dumps(dict(header, type="text/plain", path=k), sort_keys=False)
                    yield i
