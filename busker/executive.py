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
from busker.types import Completion
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

    @staticmethod
    def activate(
        exenv: ExecutionEnvironment,
        processes: int = None, maxtasksperchild: int = None,
        initializer: Callable = None
    ):
        context = multiprocessing.get_context("spawn")
        context.set_executable(exenv.interpreter)

        pool = context.Pool(processes=processes, maxtasksperchild=maxtasksperchild)
        manager = multiprocessing.managers.SyncManager(ctx=context)

        env = dataclasses.replace(exenv, pool=None, manager=None, queue=None)
        manager.start(initializer=initializer, initargs=dataclasses.astuple(env))

        try:
            exenv.queue.close()
        except AttributeError:
            pass

        exenv.pool = pool
        exenv.manager = manager
        exenv.queue = manager.Queue()

        return exenv

    @staticmethod
    def shutdown(exenv: ExecutionEnvironment):
        try:
            exenv.queue.close()
        except AttributeError:
            pass

        try:
            exenv.manager.shutdown()
            exenv.pool.terminate()
        except AttributeError:
            pass
        finally:
            exenv.queue = None
            exenv.manager = None
            exenv.pool = None
            return exenv

    def __init__(
            self, *args,
            maxlen: int = 24,
            processes: int = None, maxtasksperchild: int = None,
            **kwargs
        ):
        super().__init__(*args, maxlen=maxlen, **kwargs)
        exenv = self.build(sys.executable)
        self.activate(
            exenv,
            initializer=self.initializer,
            **kwargs
        )

    @property
    def active(self) -> ExecutionEnvironment:
        return next((exenv for exenv in self.registry.values() if exenv.manager), None)

    def initializer(self, location: pathlib.Path, interpreter: pathlib.Path, config: dict, *args):
        self.log(f"Initializing execution environment at {location!s}")

    def build(
        self,
        interpreter: str | pathlib.Path,
        location: pathlib.Path=None,
    ):
        interpreter = pathlib.Path(interpreter)

        location = location or interpreter.parent.parent
        cfg = self.venv_cfg(location)
        exenv = self.registry.setdefault(
            interpreter,
            ExecutionEnvironment(
                location = location or interpreter.parent.parent,
                interpreter=interpreter,
                config=dict(self.venv_data(cfg))
            )
        )
        return exenv

    def register(self, location: pathlib.Path, queue=None, *args) -> pathlib.Path:
        cfg = self.venv_cfg(location)

        exenv = ExecutionEnvironment(
            location=location,
            config=dict(self.venv_data(cfg)),
            queue=queue,
        )
        try:
            exenv.interpreter = self.venv_exe(location, **exenv.config)
        except (AttributeError, TypeError):
            return None

        self.registry[exenv.interpreter] = exenv
        return exenv.interpreter

    def run(
        self,
        runner: Runner,
        interpreter: str | pathlib.Path = sys.executable,
        callback=None,
        error_callback=None,
        queue=None,
        **kwargs
    ):
        interpreter = pathlib.Path(interpreter)
        exenv = self.registry[interpreter]
        try:
            exenv.queue.close()
        except AttributeError:
            pass

        try:
            exenv.queue = exenv.manager.Queue()
        except AttributeError:
            pass
        finally:
            exenv.queue = queue or exenv.queue

        env = dataclasses.replace(exenv, pool=None, manager=None)
        for job in runner.jobs:
            rv = exenv.pool.apply_async(
                job, args=(env,), kwds=kwargs,
                callback=callback,
                error_callback=error_callback
            )
            rv.exenv = exenv
            yield rv

        if isinstance(runner, Callable):
            rv = runner(exenv, **kwargs)
            runner.exenv = exenv
            yield rv


class Hello(Runner):

    def say_hello(self, exenv: ExecutionEnvironment, **kwargs):
        for n in range(10):
            print("Hello, world!", file=sys.stderr)
            exenv.queue.put(n)
            time.sleep(1)
        return Completion(self, exenv, n)

    @property
    def jobs(self):
        return [self.say_hello]


if __name__ == "__main__":
    import time

    executive = Executive()
    print(executive.registry, file=sys.stderr)

    runner = Hello()
    running = next(executive.run(runner))
    while not running.ready():
        try:
            rv = running.get(timeout=2)
            print(f"{rv.data}", file=sys.stdout)
        except multiprocessing.context.TimeoutError:
            print("No uodate", file=sys.stderr)
        finally:
            items = []
            while not running.exenv.queue.empty():
                items.append(running.exenv.queue.get(block=False))
            print(f"{items=}", file=sys.stderr)

    print(f"{executive.active=}", file=sys.stderr)
    executive.shutdown(running.exenv)
