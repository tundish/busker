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

from collections import namedtuple
import concurrent.futures
import datetime
import multiprocessing
import multiprocessing.context
import multiprocessing.pool
import pathlib
import subprocess
import sys
import time
import venv


VirtualEnvironment = namedtuple(
    "VirtualEnvironment",
    ["location", "interpreter", "config", "inspected_at", "inspection"],
    defaults=[None, None, None, None],
)


class Manager:

    pools = {}

    @classmethod
    def initializer(cls, venv: VirtualEnvironment, *args):
        print(venv, *args, sep="\n", file=sys.stderr)

    @classmethod
    def pool_factory(cls, venv: VirtualEnvironment, *args, **kwargs) -> concurrent.futures.Executor:
        context = multiprocessing.get_context("spawn")
        context.set_executable(...)  # <<< set worker executable
        pool = concurrent.futures.ProcessPoolExecutor(
            mp_context=context, max_tasks_per_child=1,
            initializer=cls.initializer, initargs=(venv, *args)
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


if __name__ == "__main__":
    #rv = subprocess.check_output([sys.executable, "-m", "turtle"])
    # rv = subprocess.check_output(["ping", "-i", "12", "8.8.8.8"])
    context = multiprocessing.get_context("spawn")
    context.set_executable(sys.executable)

    # pool = concurrent.futures.ProcessPoolExecutor(mp_context=context, max_tasks_per_child=1)
    #fut = pool.submit(Remote.hello, q=q)
    #fut.add_done_callback(Local.bye)
    #print(fut.result(timeout=2))
    #pool.shutdown(wait=True, cancel_futures=True)
    pool = multiprocessing.pool.Pool(processes=1, maxtasksperchild=1, context=context)
    ar = pool.apply_async(Remote.hello, callback=Local.done, error_callback=Local.error)
    while not ar.ready():
        try:
            rv = ar.get(timeout=2)
            print(f"{rv=}")
        except multiprocessing.context.TimeoutError:
            print("Nope")
    pool.terminate()
