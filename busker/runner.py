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
import concurrent.futures
import logging
import pathlib
import sys
import sysconfig
import tomllib


class Runner:

    executor = concurrent.futures.ProcessPoolExecutor()

    @staticmethod
    def walk_files(path: pathlib.Path, callback=None):
        callback = callback or pathlib.Path
        if path.is_dir():
            for p in path.iterdir():
                yield from Runner.walk_files(pathlib.Path(p))
        yield callback(path)

    @staticmethod
    def venv_data(text: str) -> dict:
        for line in text.splitlines():
            bits = line.partition("=")
            if bits[1] == "=":
                yield (bits[0].strip(), bits[2].strip())

    @staticmethod
    def venv_exe(path: pathlib.Path, **kwargs) -> pathlib.Path:
        scheme = sysconfig.get_default_scheme()
        script_path = pathlib.Path(sysconfig.get_path("scripts", scheme))
        exec_path = pathlib.Path(kwargs.get("executable", ""))
        return path.joinpath(script_path.name, exec_path.name)

    @staticmethod
    def venv_cfg(path: pathlib.Path, name="pyvenv.cfg") -> str:
        if path.is_dir():
            path = path.joinpath(name)

        if path.is_file() and path.name == name:
            return rv.read_text()
        else:
            return ""

