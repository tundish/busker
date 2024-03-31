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
import importlib.metadata
import logging
import pathlib
import subprocess
import sys
import time
import tomllib
import typing
import uuid
import venv

from busker.types import Completion
from busker.types import ExecutionEnvironment


class Runner:

    def __init__(self, uid: uuid.UUID = None, **kwargs):
        self.uid = uid or uuid.uuid4()

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
    def jobs(self) -> list | typing.Self:
        return []


class VirtualEnv(Runner):

    def __init__(self, location: pathlib.Path):
        super().__init__()
        self.location = location

    def build_virtualenv(self, this: Callable, exenv: ExecutionEnvironment, **kwargs):
        venv.create(
            self.location,
            system_site_packages=True,
            clear=True,
            with_pip=True,
            upgrade_deps=True
        )
        return Completion(self, this, exenv)

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
        return Completion(self, this, exenv)

    @property
    def jobs(self) -> list:
        return [self.build_virtualenv, self.check_virtualenv]


class Installation(Runner):

    @staticmethod
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

    def __init__(self, distribution: pathlib.Path, read_interval: int = 0.5):
        super().__init__()
        self.distribution = distribution
        self.read_interval = read_interval
        self.proc = None
        self.exenv = None

    def __call__(
        self,
        exenv: ExecutionEnvironment,
        **kwargs
    ):
        self.exenv = exenv

        args = self.pip_command_args(
            interpreter=exenv.interpreter,
            distribution=self.distribution,
        )
        self.exenv.queue.put(args)
        self.proc = subprocess.Popen(
            args,
            bufsize=1,
            shell=False,
            encoding="utf8",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=exenv.location,
            env=None,
        )
        return self.proc


class Discovery(Runner):

    def get_entry_points(self, this: Callable, exenv: ExecutionEnvironment, **kwargs):
        rv = importlib.metadata.entry_points()
        return Completion(self, this, exenv, data=rv)

    @property
    def jobs(self) -> list:
        return [self.get_entry_points]


if __name__ == "__main__":
    exenv = ExecutionEnvironment(pathlib.Path("."))
    runner = Discovery()
    result = runner.get_entry_points(runner.get_entry_points, exenv)
    scripts = result.data.select(group="console_scripts")
    print(*scripts, sep="\n")
