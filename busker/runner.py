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
import difflib
import logging
import pathlib
import re
import string
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

    def build_virtualenv(self, exenv: ExecutionEnvironment, **kwargs):
        venv.create(
            self.location,
            system_site_packages=True,
            clear=True,
            with_pip=True,
            upgrade_deps=True
        )
        return Completion(self, exenv)

    def check_virtualenv(self, exenv: ExecutionEnvironment, repeat=100, interval=2, **kwargs):
        values = []
        while len(values) < repeat:
            files = list(self.walk_files(self.location))
            values.append(len(files))
            exenv.queue.put(values[-1])
            if len(values) > 3 and values[-3] == values[-1] and values[-1] <= max(values):
                break
            else:
                time.sleep(interval)
        return Completion(self, exenv)

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
        rv = [interpreter, "-m", "pip", "install", "--upgrade", "--upgrade-strategy", "eager", specification]
        if update:
            rv.insert(4, "--upgrade")
        return rv

    def __init__(self, distribution: pathlib.Path, read_interval: int = 0.5):
        super().__init__()
        self.distribution = distribution
        self.read_interval = read_interval
        self.proc = None

    def __call__(
        self,
        exenv: ExecutionEnvironment,
        **kwargs
    ):
        args = self.pip_command_args(
            interpreter=exenv.interpreter,
            distribution=self.distribution,
        )
        exenv.queue.put(args)
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

    @staticmethod
    def command() -> str:
        return "; ".join([
            "import importlib.metadata as im",
            "print(*[i.name for i in im.entry_points(group='console_scripts')], sep='\\n')",
        ])

    @staticmethod
    def filter_entry_points(items):
        excluded = re.compile("(pip[0-9.]*)|(hypercorn)|(wheel)$")
        return [i for i in items if not excluded.match(i)]

    @staticmethod
    def sort_entry_points(items, like="cli"):
        def comparison(text):
            matcher = difflib.SequenceMatcher(string.punctuation.count, like, text)
            return matcher.ratio()
        return sorted(items, key=comparison, reverse=True)

    def __call__(
        self,
        exenv: ExecutionEnvironment,
        **kwargs
    ):
        args = [exenv.interpreter, "-c", self.command()]
        exenv.queue.put(args)
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


class Server(Runner):

    @staticmethod
    def args(
        location: pathlib.Path,
        entry_point: str,
        host: str,
        port: int
    ) -> list:
        rv = [
            str(location.joinpath(entry_point)),
        ]
        if host:
            rv.extend(["--host", host])
        if port:
            rv.extend(["--port", str(port)])
        return rv

    def __init__(
        self,
        entry_point: str,
        host: str = None,
        port: int = None,
    ):
        super().__init__()
        self.entry_point = entry_point
        self.host = host
        self.port = port

    def __call__(
        self,
        exenv: ExecutionEnvironment,
        **kwargs
    ):
        args = self.args(exenv.interpreter.parent, self.entry_point, self.host, self.port)
        exenv.queue.put(args)
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

    @property
    def url(self):
        return f"http://{self.host}:{self.port}"


if __name__ == "__main__":
    import queue
    exenv = ExecutionEnvironment(pathlib.Path("."), interpreter=sys.executable, queue=queue.Queue())
    runner = Discovery()
    proc = runner(exenv)
    out, err = proc.communicate()
    entry_points = runner.filter_endpoints([i.strip() for i in out.splitlines()])
    print(*entry_points, sep="\n")
