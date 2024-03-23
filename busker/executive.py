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
import venv

from busker.runner import Runner


@dataclasses.dataclass
class ExecutionEnvironment:
    location: pathlib.Path
    interpreter: pathlib.Path = None
    config: dict = None
    pool: multiprocessing.pool.Pool = None
    manager: multiprocessing.managers.SyncManager = None
    queue: multiprocessing.Queue = None


class Executive:

    registry = {}

    @classmethod
    def initializer(cls, location: pathlib.Path, interpreter: pathlib.Path, config: dict, *args):
        print(f"{interpreter=}", *args, sep="\n", file=sys.stderr)

    @classmethod
    def register(
        cls,
        interpreter: str | pathlib.Path, location: pathlib.Path=None, config: dict=None,
        processes: int = None, maxtasksperchild: int = None
    ):
        interpreter = pathlib.Path(interpreter)
        exenv = cls.registry.setdefault(
            interpreter,
            ExecutionEnvironment(
                location = location or interpreter.parent.parent,
                interpreter=interpreter,
                config=config,
            )
        )
        if exenv.queue:
            return exenv

        context = multiprocessing.get_context("spawn")
        context.set_executable(exenv.interpreter)

        pool = context.Pool(processes=processes, maxtasksperchild=maxtasksperchild)
        manager = multiprocessing.managers.SyncManager(ctx=context)

        manager.start(initializer=cls.initializer, initargs=dataclasses.astuple(exenv))
        exenv.pool = pool
        exenv.manager = manager
        exenv.queue = manager.Queue()
        return exenv

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

    def __init__(self):
        self.register(sys.executable)

    def callback(self, result):
        return

    def error_callback(self, exc: Exception, *args):
        return

    def run(self, interpreter: str | pathlib.Path, *jobs: tuple[Runner], **kwargs):
        interpreter = pathlib.Path(interpreter)
        exenv = self.registry[interpreter]
        for job in jobs:
            env = dataclasses.replace(exenv, pool=None, manager=None)
            rv = exenv.pool.apply_async(
                job, args=(env,), kwds=kwargs,
                callback=self.callback, error_callback=self.error_callback
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


class Example:

    def update_progress(self, path: pathlib.Path, future=None):
        files = list(self.walk_files(path))
        self.activity.append(len(files))

        if future and not future.done():
            for bar in self.controls.progress:
                # TODO: Better approximation of progress
                half = 50 if self.activity[-1] < max(self.activity) else 0
                bar["value"] = min(half + len(self.activity) * 8, 100)

            self.frame.after(1500, self.update_progress, path, future)

    def on_build(self):
        path = pathlib.Path(self.controls.entry[0].get())

        future = self.executor.submit(
            venv.create,
            path,
            system_site_packages=True,
            clear=True,
            with_pip=True,
            upgrade_deps=True
        )
        future.add_done_callback(self.on_complete)
        self.update_progress(path, future)


if __name__ == "__main__":
    import time

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


    executive = Executive()
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
