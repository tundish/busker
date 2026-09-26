#!/usr/bin/env python
#   encoding: utf-8

# Copyright (C) 2026 D E Haynes
# This file is part of busker.

# Busker is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# Busker is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with busker.
# If not, see <https://www.gnu.org/licenses/>.

from concurrent.futures import ThreadPoolExecutor
import contextvars
import difflib
import logging
import queue
import time
from types import SimpleNamespace as SN
import sched

try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import font as tkfont
    from busker.model.journal import Journal
except ModuleNotFoundError:
    tk = None
    ttk = None
    tkfont = None

# https://python-patterns.guide/
# https://streamkap.com/resources-and-guides/streaming-api-design-patterns
# https://anyio.readthedocs.io/en/stable/why.html
# https://four.htmx.org/
# https://www.youtube.com/watch?v=lASLZ9TgXyc
# https://vorpus.org/blog/some-thoughts-on-asynchronous-api-design-in-a-post-asyncawait-world/

"""
def some_sync_generator(path):
    with open(path) as ...:
        yield ...

# DON'T do this
for obj in some_sync_generator(path):
    ...

# DO do this
from contextlib import closing
with closing(some_sync_generator(path)) as tmp:
    for obj in tmp:

"""

# Order of implementation
# Marker
# + visit counter for every path
#
# Content
# + style
# + theme
# + pulse - allow eg: (0, 1E99) for one-shots
#
# types text/speechmark or text/plain so factory param required

# CSS variables conventions:
#
#
"""
--color-ink-gravity: hsl(282.86, 0%, 6.12%);
--color-ink-shadows: hsl(293.33, 0%, 22.75%);
--color-ink-lolight: hsl(203.39, 0%, 31.96%);
--color-ink-midtone: hsl(203.39, 0%, 41.96%);
--color-ink-hilight: hsl(203.06, 0%, 56.47%);
--color-ink-washout: hsl(66.77, 0%, 82.75%);
--color-ink-glamour: hsl(50.00, 0%, 100%);

--param-ink-gravity-hue-pick-1: 282.86
--param-ink-shadows-hue-pick-1: 293.33
--param-ink-lolight-hue-pick-1: 203.39
--param-ink-midtone-hue-pick-1: 203.39
--param-ink-hilight-hue-pick-1: 203.06
--param-ink-washout-hue-pick-1: 66.77
--param-ink-glamour-hue-pick-1: 50.00

Use these for collections of related parameters:

... -pair-1
... -pair-2
... -trio-1
... -trio-2
... -trio-3
... -quad-1
... -quad-2
... -quad-3
... -quad-4

etc.

"""

class Resident:
    "A core-resident actor"

    # Shared among subclasses within the same thread
    shared = contextvars.ContextVar("shared")

    executor = ThreadPoolExecutor()

    """
    def __init__(self, cmd_queue: asyncio.Queue() = None, msg_queue: asyncio.Queue() = None):
        self.cmd_queue = cmd_queue or asyncio.Queue()
        self.msg_queue = msg_queue or asyncio.Queue()

    def __iter__(self):
        "Or is __aiter__ a better fit?"
        return
        yield

    async def __aiter__(self):
        "async for i in ... means client code must be async too."
        for n in range(10):
            await asyncio.sleep(0.5)
            yield n

    async def __call__(self, **kwargs):
        async with asyncio.TaskGroup() as tasks:
            ...
    """


class Engine(Resident):

    ignored_words = ("a", "an", "any", "her", "his", "my", "some", "the", "their")

    class Exclamation(Exception):
        pass

    class BusyError(Exception):
        "Call add_note as to why"
        pass

    class InternalError(Exception):
        """
        try:
            ...
        except ValueError as err:
            err.add_note(...)
            raise InternalError from err

        """
        pass

    def __init__(self, journal: Journal = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.queues = (queue.Queue(maxsize=1), queue.Queue())
        self.journal = journal
        self.future = None
        self.listen = True

        """
        if journal:
            self.clocks = dict(self.set_clocks(journal))
        """

    @property
    def stats(self):
        path = self.journal.uri.resolve()
        return SN(
            path=path,
            mtime=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(path.stat().st_mtime)),
            size=f"{path.stat().st_size/1E3:0.3f}K" if path.is_file() else "",
        )

    def __repr__(self):
        stats = self.stats
        return (
            f"{self.__class__.__name__}"
            f" {stats.mtime}"
            f" {stats.path.as_uri()}"
            f" {stats.size}"
        )

    def __call__(self, timeout=2, **kwargs):
        while self.listen:
            try:
                cmd = self.queues[0].get(block=True, timeout=timeout)
            except queue.Empty:
                continue

            self.logger.debug(f"{cmd=}")

            stream = []
            # TODO:
            # * read markers
            marking = self.journal.marking
            if not marking:
                from busker.model.types import ElementType
                # TODO: Invoke DRC plugin?
                self.logger.warning(f"Journal has no marking")
                for path, values in self.journal.adaptor.data.items():
                    self.logger.debug(f"FRAME at path {path}:")
                    for item in values:
                        self.logger.debug(item)
                        bit = (getattr(item, "type", None) == ElementType.MARKING.value)
                        self.logger.debug(f"Marker? {bit}")

            stream.append(marking)

            # * check actions
            try:
                stream.append(self.journal.actions)
            except AttributeError:
                # No Syntax lens. What now?
                pass

            # * call action, or
            # * call unknown

            for item in stream:
                try:
                    self.queues[1].put(item, block=False)
                except queue.Full:
                    # TODO: Roll back?
                    pass

            self.queues[0].task_done()

    def run(self, **kwargs):
        if not self.journal:
            raise self.InternalError("No journal attached")
        self.future = self.executor.submit(self, **kwargs)
        self.future.add_done_callback(self.cleanup)
        return self

    def cleanup(self, future):
        self.logger.info("Terminated")
        try:
            self.logger.debug(f"return: {future.result()!s}")
        except Exception as err:
            self.logger.warning(err, exc_info=True)


# NOTE: use for ideas.

    @staticmethod
    def split_to_words(text: str, preserver=".", discard=None):
        discard = discard or set()
        return [
            i.strip()
            for i in text.rstrip(preserver).lower().split()
            if i not in discard or text.endswith(preserver)
        ]

    def match_text_to_phrases(self, text: str, phrases: list[str], precision=0.95):
        words = self.split_to_words(text, discard=self.ignored_words)
        print(f"{words=}")
        return difflib.get_close_matches(
            " ".join(words), phrases, cutoff=precision
        ) or difflib.get_close_matches(text.strip(), phrases, cutoff=precision)

    @staticmethod
    def set_clocks(journal):
        for marker in journal.marking:
            marker.scheduler = sched.scheduler()
            yield marker["name"], marker

    def cmd(self, text: str, marker: dict, precision=0.95, **kwargs):
        actions = self.rht.actions(marker.parent.path)
        matches = self.match_text_to_phrases(text, actions)
        if not matches:
            self.logger.debug(f"No match for text '{text}'")
            return
        self.logger.info(f"Selecting first of matches {matches}")
        element, kwargs = actions[matches[0]]

        code = compile(element.handler, format(marker.parent.path), mode="exec")
        l = dict(kwargs, journal=self.rht, marker=marker)
        g = dict(logging=logging, Exclamation=self.Exclamation)
        try:
            exec(code, locals=l, globals=g)
        except self.Exclamation as report:
            self.logger.info(report)
        except Exception as err:
            self.logger.warning(err, exc_info=True)
        # Advance tick

    def put(self, *args, delay=0, **kwargs):
        return [
            marker.scheduler.enter(
                delay, n, self.cmd, argument=(arg, marker), kwargs=kwargs
            )
            for n, arg in enumerate(args)
            for marker in self.clocks.values()
        ]

    def step(self, **kwargs):
        import time
        for marker in self.clocks.values():
            delta = 0
            then = time.time()
            while delta is not None:
                time.sleep(delta)
                delta = marker.scheduler.run(blocking=False)
