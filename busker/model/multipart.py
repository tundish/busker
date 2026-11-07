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

"""

> One thing leads to the next thing, it leads to the next thing, it leads to the next thing.
>
> -- <cite>Roots Manuva</cite>

A Busker multipart document is a human-readable (UTF-8) text file.
It contains one or more sections. In order that the boundary of a section may be identified,
each one is preceded by a separator.

Document separators
-------------------

A separator is a single line of text which corresponds to a valid JSON object.
The first attribute of the JSON object is a 'seal' which is consistent throughout the
document and which serves to distinguish a separator from other data in the document.

The attributes required in a separator are tabulated here:

|Attribute  |Purpose                                            |Example           |Note                                                            |
|----------:|:-------------------------------------------------:|:----------------:|:---------------------------------------------------------------|
|seal       |Signifies JSON data is a section separator         |20261101164759    | Number or String                                               |
|type       |The type of data contained in the section          |text/plain        | [RFC 2046](https://www.rfc-editor.org/info/rfc2046) media type |
|path       |A hierarchical path to which the section belongs   |[1, 2, 3]         | Array of Number or String                                      |

Consequently, the first line of a Multipart document must be an entire JSON object,
and its *seal* value is the one used for disambiguation, eg:

`{"seal": 20261101164759, "busker": "0.39.0", "type": "text/plain", "path": [1, 2, 3]}`

The location of sections in the document is declared by the *path* attribute.
The ordered collection of sections at each path is called a *frame*.

"""
import ast
from collections.abc import Generator
from collections.abc import Mapping
from collections import defaultdict
from collections import UserDict
from collections import UserList
from collections import UserString
import json
import logging
import pathlib
import pprint
import re

from busker import __version__
from busker.model.types import Adaptor
from busker.model.types import BackendType
from busker.model.types import Chain


class Multipart(Adaptor):

    def __init__(
        self, *args,
        factory: dict = None,
        default_path: tuple = None,
    ):
        """
        Contruct an object representing a Multipart document.

        `factory`
        :   A dictionary mapping generic types from the document to the object
            classes which will be held in memory.

        `default_path`
        :   A default value for document section paths.

        """
        self._logger = logging.getLogger("busker.multipart")
        self._mark_regex = re.compile(r"^\{.+?\}$", re.MULTILINE)

        self._seal = id(self)
        self._path = default_path or tuple()

        self._factory = {dict: dict, list: list, str: str}
        self._factory.update(factory or {})

        self.backend: BackendType = BackendType.RHT_TXT
        """The declared backend type."""
        self.data: dict = defaultdict(self._factory[list])
        """The raw document data."""
        self.data[self._path].extend(args)

    def __str__(self):
        return "\n".join(str(i) if isinstance(i, UserString) else i for i in self.dump())

    @property
    def header(self) -> dict:
        """The static attributes of the document separator."""
        if self._path is None:
            return dict(seal=self._seal, type=None, busker=__version__)
        else:
            return dict(seal=self._seal, type=None, busker=__version__, path=self._path[:])

    @property
    def tree(self) -> dict:
        """Expansion of the document as a nested tree of frames."""
        rv = dict()
        done = dict()
        paths = list(self.data)
        for path in paths:
            node = rv
            for n, key in enumerate(path):
                pos = tuple(path[:n + 1])
                if pos in done:
                    node = done[pos]
                    continue

                try:
                    frame = self.data[pos]
                    node[key] = Chain(*(i for i in frame if isinstance(i, Mapping)))
                except KeyError:
                    node[key] = Chain()

                node[key] = node[key].new_child()
                done[pos] = node[key]
        return rv

    def load(self, uri: str | pathlib.Path) -> str:
        """
        Load the document from a file.

        `uri`
        : A path-like object to a document file.

        """
        return uri.read_text()

    def save(self, uri: str | pathlib.Path) -> str:
        """
        Save the document to a file.

        `uri`
        : A path-like object to the new file.

        """
        text = str(self)
        uri.write_text(text)
        return text

    def scan(
        self,
        text: str,
        header_length=255,
        code_types=set(("application/x-python-code", "application/x-python", "application/python", "code/python")),
        data_types=set(("application/json", "text/json", "data/json", "text/python", "text/x-python", "data/python")),
        text_types=set(("text/plain", "text/markdown", "text/speechmark"))
    ) -> Generator[dict]:
        """
        Read a multipart document and separate it into sections.

        `text`
        : The text of the document.

        `header_length`
        : A limit on the length of the first line of the document.

        `code_types`
        : A collection of RFC 2046-style media types to be treated as executable code.

        `data_types`
        : A collection of RFC 2046-style media types to be treated as data structures.

        `text_types`
        : A collection of RFC 2046-style media types to be treated as text.

        This method is a generator of document sections.

        """
        delimiters = list(self._mark_regex.finditer(text))
        if not delimiters:
            self._logger.error("No delimiters found")
            return
        if (pos := delimiters[0].start()) != 0:
            self._logger.error(f"Header does not lead. Pos: {pos}")
            return

        try:
            header = json.loads(delimiters[0][0])
        except json.JSONDecodeError:
            self._logger.error(f"Invalid Header. Pos: {pos}")
            return

        seal = header.get("seal")
        if seal:
            self._seal = seal
        else:
            self._logger.error(f"No seal found. Pos: {pos}")
            return

        for n, d in enumerate(delimiters):
            if (pos := d.end()) - d.start() > header_length:
                self._logger.error(f"Delimiter too long. Pos: {pos}")
                return

            try:
                data = json.loads(d[0])
            except json.JSONDecodeError:
                self._logger.error(f"Invalid Delimiter. Pos: {pos}")
                return

            if data.get("seal") != seal:
                self._logger.error(f"Seal mismatch. Pos: {pos}")
                return

            if len(delimiters) - n > 1:
                data["payload"] = payload = text[d.end(): delimiters[n + 1].start()]
            else:
                data["payload"] = payload = text[d.end():]

            if data.get("type") in code_types:
                try:
                    path = format(data.get("path", self._path))
                except ValueError as err:
                    self._logger.error(f"Invalid Path. Pos: {d.end()}", exc_info=True)
                    return

                try:
                    data["payload"] = payload = ast.parse(payload, filename=path, mode="exec")
                except SyntaxError as err:
                    self._logger.error(f"Invalid Code. Pos: {d.end()}", exc_info=True)
                    return

            elif data.get("type") in data_types:
                parser = ast.literal_eval if "python" in data["type"] else json.loads
                try:
                    payload = parser(payload)
                    if isinstance(payload, Mapping) and payload.get("type") in self._factory:
                        factory = self._factory[payload["type"]]
                        self._logger.debug(f"Data item {n}. Type: {factory.__name__}")
                        payload = factory(**payload)
                    elif type(payload) in self._factory:
                        factory = self._factory[type(payload)]
                        self._logger.debug(f"Data item {n}. Type: {factory.__name__}")
                        payload = factory(payload)
                    data["payload"] = payload
                except (SyntaxError, ValueError) as err:
                    self._logger.error(f"Invalid Literal. Pos: {d.end()}", exc_info=True)
                    return
                except json.JSONDecodeError:
                    self._logger.error(f"Invalid Data. Pos: {d.end()}", exc_info=True)
                    return

            elif type(payload) in self._factory:
                data["payload"] = payload = self._factory[type(payload)](payload)

            path = tuple(data.get("path", self._path))
            self.data[path].append(payload)
            yield data

    def dump(self, safe: bool = False) -> Generator[str]:
        """
        Write the document as a sequence of strings.

        `safe`
        :   If True, limit the depth of data structures.

        This method is a generator of text blocks.

        """
        header = self.header
        for n, (k, v) in enumerate(self.data.items()):
            if n == 1:
                header.pop("busker", None)
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
