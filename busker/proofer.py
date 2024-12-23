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
#! /usr/bin/env python
# encoding: utf-8

from collections import Counter
from collections import namedtuple
import pathlib
import re
import string
import tomllib


class Proofer:

    Script = namedtuple("Script", ["path", "text", "tables", "errors"], defaults=["", None, None])

    #  Copied from speechmark.py
    cue_matcher = re.compile(
        """
    ^<                              # Opening bracket
    (?P<role>[^\.:\\?# >]*)         # Role
    (?P<directives>[^\:\\?# >]*)    # Directives
    (?P<mode>[^\\?# >]*)            # Mode
    (?P<parameters>[^# >]*)         # Parameters
    (?P<fragments>[^ >]*)           # Fragments
    >                               # Closing bracket
    """,
        re.VERBOSE,
    )

    @classmethod
    def read_toml(cls, text: str, errors: dict = None, **kwargs) -> Script:
        errors = errors or {}
        tables = {}
        try:
            tables = tomllib.loads(text, **kwargs)
        except tomllib.TOMLDecodeError as e:
            line = int(next((i for i in str(e).replace(",", " ").split() if i.isdigit()), "0"))
            errors[line] = e
        return cls.Script(None, text, tables, errors)

    @classmethod
    def read_script(cls, path: pathlib.Path, **kwargs):
        try:
            text = path.read_text()
        except FileNotFoundError as e:
            return cls.Script(path.resolve(), errors={0: e})

        return cls.read_toml(text, **kwargs)._replace(path=path.resolve())

    @staticmethod
    def check_stage(*scripts: tuple[Script], **kwargs):
        witness = Counter()
        for script in scripts:
            if not isinstance(script.tables.get("puzzles"), list):
                script.errors[0] = "No puzzles detected"
            else:
                for n, key in enumerate(("label", "realm")):
                    if key not in script.tables:
                        script.errors[n] = f"Puzzle strand is missing attribute '{key}'"

            if any(puzzle.get("init") for puzzle in script.tables.get("puzzles", [])):
                witness["init"] += 1
            if any(puzzle.get("states") for puzzle in script.tables.get("puzzles", [])):
                witness["states"] += 1

            if script is scripts[-1] and not witness["init"] and not witness["states"]:
                script.errors[0] = "At least one puzzle must contain states or an 'init' table"

            yield script

    @classmethod
    def check_scene(cls, script: Script):
        formatter = string.Formatter()
        for n, line in enumerate(script.text.splitlines()):
            cue = cls.cue_matcher.match(line)
            try:
                if cue["role"] and cue["role"] not in script.tables:
                    script.errors[n + 1] = f"Cue for '{cue['role']}' but no role declared"
            except TypeError:
                pass

            for result in formatter.parse(line):
                reference = result[1]
                try:
                    path = reference.split(".")
                    role = path[0]
                except (AttributeError, IndexError):
                    continue

                if role not in script.tables:
                    script.errors[n + 1] = f"Role '{role}' referenced but not declared"
        return script
