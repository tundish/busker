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

from collections.abc import Callable
from collections import defaultdict
from collections import deque
import concurrent.futures
import logging
import pathlib
import sys
import time
import tomllib
import venv


from busker.types import Completion
from busker.types import ExecutionEnvironment


class Runner:

    @staticmethod
    def walk_files(path: pathlib.Path, callback=None):
        callback = callback or pathlib.Path
        if path.is_dir():
            try:
                for p in path.iterdir():
                    yield from Runner.walk_files(pathlib.Path(p))
            except Exception:
                pass
        yield callback(path)

    @property
    def jobs(self) -> list:
        return []


class VirtualEnv(Runner):

    def __init__(self, location: pathlib.Path):
        self.location = location

    def build_virtualenv(self, this: Callable, exenv: ExecutionEnvironment, **kwargs):
        venv.create(
            self.location,
            system_site_packages=True,
            clear=True,
            with_pip=True,
            upgrade_deps=True
        )
        return Completion(this, exenv)

    def check_virtualenv(self, this: Callable, exenv: ExecutionEnvironment, repeat=100, interval=2, **kwargs):
        values = []
        while len(values) < repeat:
            files = list(self.walk_files(self.location))
            values.append(len(files))
            exenv.queue.put(values[-1])
            if len(values) > 3 and values[-3] == values[-1] and values[-1] <= max(values):
                break
            else:
                time.sleep(interval)
        return Completion(this, exenv)

    @property
    def jobs(self) -> list:
        return [self.build_virtualenv, self.check_virtualenv]


class Installation(Runner):

    def pip_command_args(
        interpreter: pathlib.Path,
        distribution: pathlib.Path,
        dependencies: list = ["test"],
        update=False,
    ) -> list[str]:
        specification = f"{distribution}" + ("[{0}]".format(",".join(dependencies)) if dependencies else "")
        rv = [interpreter, "-m", "pip", "install", specification]
        if update:
            rv.insert(4, "--upgrade")
        return rv

    def __init__(self, distribution: pathlib.Path):
        self.distribution = distribution

    def install_distribution(self, this: Callable, exenv: ExecutionEnvironment, **kwargs):
        args = self.pip_command_args(
            interpreter=exenv.interpreter,
            distribution=self.distribution,
        )
        proc = subprocess.Popen(
            args,
            bufsize=1,
            shell=False,
            encodimg="utf8",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=exenv.location,
            env=None,
        )
        return Completion(this, exenv)

    def check_installation(self, this: Callable, exenv: ExecutionEnvironment, repeat=100, interval=2, **kwargs):
        values = []
        while len(values) < repeat:
            files = list(self.walk_files(self.location))
            values.append(len(files))
            exenv.queue.put(values[-1])
            if len(values) > 3 and values[-3] == values[-1] and values[-1] <= max(values):
                break
            else:
                time.sleep(interval)
        return Completion(this, exenv)

    @property
    def jobs(self) -> list:
        return [self.install_distribution, self.check_installation]
