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
import datetime
import multiprocessing
import multiprocessing.context
import multiprocessing.managers
import multiprocessing.pool
import pathlib
import subprocess
import sys
import time
import venv


@dataclasses.dataclass
class ExecutionEnvironment:
    location: pathlib.Path
    interpreter: pathlib.Path = None
    config: dict = None
    pool: multiprocessing.pool.Pool = None
    manager: multiprocessing.managers.SyncManager = None
    queue: multiprocessing.Queue = None


class Executive:

    exenvs = {}

    @classmethod
    def initializer(cls, location: pathlib.Path, interpreter: pathlib.Path, config: dict, *args):
        print(f"{interpreter=}", *args, sep="\n", file=sys.stderr)

    @classmethod
    def pool_factory(cls, exenv: ExecutionEnvironment, *args, **kwargs):
        context = multiprocessing.get_context("spawn")
        context.set_executable(...)  # <<< set worker executable
        pool = concurrent.futures.ProcessPoolExecutor(
            mp_context=context, max_tasks_per_child=1,
            initializer=cls.initializer, initargs=(exenv, *args)
        )
        return pool


class Local:

    @staticmethod
    def bye(*args, **kwargs):
        print("Bye!", file=sys.stderr)

    @staticmethod
    def done(*args, **kwargs):
        print("Done.", file=sys.stderr)

    @staticmethod
    def error(error, *args, **kwargs):
        print(f"{error=}", file=sys.stderr)


class Remote:

    @staticmethod
    def hello(*args, q=None, **kwargs):
        for n in range(10):
            print("Hello.", file=sys.stderr)
            q.put(n)
            time.sleep(1)
        return n


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


class Runner:

    def callback(self, result):
        return

    def error_callback(self, exc: Exception, *args):
        return

    @property
    def jobs(self) -> list:
        return []

    def run(self, exenv: ExecutionEnvironment, *jobs, **kwargs):
        for job in jobs:
            env = dataclasses.replace(exenv, pool=None, manager=None)
            yield exenv.pool.apply_async(
                job, args=(env,), kwds=kwargs,
                callback=self.callback, error_callback=self.error_callback
            )


class Hello(Runner):

    def say_hello(self, exenv: ExecutionEnvironment, **kwargs):
        for n in range(10):
            print("Hello.", file=sys.stderr)
            exenv.queue.put(n)
            time.sleep(1)
        return n

    @property
    def jobs(self):
        return [self.say_hello]


if __name__ == "__main__":

    exenv = ExecutionEnvironment(pathlib.Path(sys.executable).parent.parent, pathlib.Path(sys.executable))
    context = multiprocessing.get_context("spawn")
    context.set_executable(exenv.interpreter)

    pool = context.Pool(processes=1, maxtasksperchild=1)
    manager = multiprocessing.managers.SyncManager(ctx=context)

    manager.start(initializer=Executive.initializer, initargs=dataclasses.astuple(exenv))
    exenv.pool = pool
    exenv.manager = manager
    exenv.queue = manager.Queue()

    runner = Hello()
    running = set(runner.run(exenv, *runner.jobs))
    while not all(r.ready() for r in running):
        for result in running:
            try:
                rv = result.get(timeout=2)
                print(f"{rv=}")
            except multiprocessing.context.TimeoutError:
                print("Nope")
            finally:
                items = []
                while not exenv.queue.empty():
                    items.append(exenv.queue.get(block=False))
                print(f"{items=}")
    try:
        exenv.queue.close()
    except AttributeError:
        # Windows
        pass
    exenv.manager.shutdown()
    exenv.pool.terminate()
