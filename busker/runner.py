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
import time
import tomllib
import venv


from busker.types import ExecutionEnvironment


class Runner:

    @staticmethod
    def walk_files(path: pathlib.Path, callback=None):
        callback = callback or pathlib.Path
        if path.is_dir():
            for p in path.iterdir():
                yield from Runner.walk_files(pathlib.Path(p))
        yield callback(path)

    @property
    def jobs(self) -> list:
        return []


class VirtualEnv(Runner):

    def __init__(self, location: pathlib.Path):
        self.location = location

    def build_virtualenv(self, exenv: ExecutionEnvironment, **kwargs):
        venv.create(
            self.location,
            system_site_packages=True,
            clear=True,
            with_pip=True,
            upgrade_deps=True
        )

    def check_virtualenv(self, exenv: ExecutionEnvironment, repeat=100, interval=2, **kwargs):
        n = 0
        while n < repeat:
            n += 1
            files = list(self.walk_files(self.location))
            exenv.queue.put(len(files))
            time.sleep(interval)

    @property
    def jobs(self) -> list:
        return [self.build_virtualenv, self.check_virtualenv]
