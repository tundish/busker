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

import dataclasses
import multiprocessing
import multiprocessing.context
import multiprocessing.managers
import multiprocessing.pool
import pathlib
import sys
import sysconfig
import time
import venv

from busker.history import SharedHistory
from busker.runner import Runner
from busker.types import ExecutionEnvironment


class Executive(SharedHistory):

    registry = {}

    @staticmethod
    def venv_cfg(path: pathlib.Path, name="pyvenv.cfg") -> str:
        if path.is_dir():
            path = path.joinpath(name)

        if path.is_file() and path.name == name:
            return path.read_text()
        else:
            return ""

    @staticmethod
    def venv_data(text: str) -> dict:
        for line in text.splitlines():
            bits = line.partition("=")
            if bits[1] == "=":
                yield (bits[0].strip(), bits[2].strip())

    @staticmethod
    def venv_exe(location: pathlib.Path, **kwargs) -> pathlib.Path:
        scheme = sysconfig.get_default_scheme()
        script_path = pathlib.Path(sysconfig.get_path("scripts", scheme))
        exec_path = pathlib.Path(kwargs.get("executable", ""))
        return location.joinpath(script_path.name, exec_path.name)

    def __init__(self, *args, maxlen: int = 24, **kwargs):
        super().__init__(*args, maxlen=maxlen, **kwargs)
        self.register(sys.executable)

    def callback(self, result):
        return

    def error_callback(self, exc: Exception, *args):
        return

    def initializer(self, location: pathlib.Path, interpreter: pathlib.Path, config: dict, *args):
        self.log(f"Initializing execution environment at {location!s}")

    def register(
        self,
        interpreter: str | pathlib.Path, location: pathlib.Path=None, config: dict=None,
        processes: int = None, maxtasksperchild: int = None
    ):
        interpreter = pathlib.Path(interpreter)
        exenv = self.registry.setdefault(
            interpreter,
            ExecutionEnvironment(
                location = location or interpreter.parent.parent,
                interpreter=interpreter,
                config=config,
            )
        )
        if exenv.queue:
            return exenv

        cfg = self.venv_cfg(exenv.location)
        exenv.config = dict(self.venv_data(cfg))

        context = multiprocessing.get_context("spawn")
        context.set_executable(exenv.interpreter)

        pool = context.Pool(processes=processes, maxtasksperchild=maxtasksperchild)
        manager = multiprocessing.managers.SyncManager(ctx=context)

        manager.start(initializer=self.initializer, initargs=dataclasses.astuple(exenv))
        exenv.pool = pool
        exenv.manager = manager
        exenv.queue = manager.Queue()
        return exenv

    def run(
        self,
        interpreter: str | pathlib.Path,
        *jobs: tuple[Runner],
        callback=None,
        error_callback=None,
        **kwargs
    ):
        interpreter = pathlib.Path(interpreter)
        exenv = self.registry[interpreter]
        for job in jobs:
            env = dataclasses.replace(exenv, pool=None, manager=None)
            rv = exenv.pool.apply_async(
                job, args=(env,), kwds=kwargs,
                callback=callback or self.callback,
                error_callback=error_callback or self.error_callback
            )
            rv.environment = env
            yield rv

    def shutdown(self):
        while self.registry:
            key, exenv = self.registry.popitem()
            try:
                exenv.queue.close()
            except AttributeError:
                # Windows
                pass
            exenv.manager.shutdown()
            exenv.pool.terminate()


class Hello(Runner):

    def say_hello(self, exenv: ExecutionEnvironment, **kwargs):
        for n in range(10):
            print("Hello, world!", file=sys.stderr)
            exenv.queue.put(n)
            time.sleep(1)
        return n

    @property
    def jobs(self):
        return [self.say_hello]


if __name__ == "__main__":
    import time

    executive = Executive()
    print(executive.registry, file=sys.stderr)

    runner = Hello()
    running = set(executive.run(sys.executable, *runner.jobs))
    while not all(r.ready() for r in running):
        for result in running:
            try:
                rv = result.get(timeout=2)
                print(f"{rv=}")
            except multiprocessing.context.TimeoutError:
                print("Nope")
            finally:
                items = []
                while not result.environment.queue.empty():
                    items.append(result.environment.queue.get(block=False))
                print(f"{items=}")

    executive.shutdown()
