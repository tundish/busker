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

import bisect
import calendar
import cmath
from collections import namedtuple
from collections import UserDict
from collections import UserList
from collections import UserString
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
import contextvars
import copy
import decimal
import fractions
import difflib
import itertools
import logging
import math
import operator
import platform
import queue
import random
import re
import sched
import statistics
import sys
import time
import textwrap
from types import SimpleNamespace as SN
import uuid
import warnings
import zoneinfo

try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import font as tkfont
except ModuleNotFoundError:
    tk = None
    ttk = None
    tkfont = None

from busker.engine.marker import Marker
from busker.engine.mechanism import Mechanism
from busker.model.journal import Journal
from busker.model.multipart import Multipart
from busker.model.types import Exclamation
from busker.model.types import Note
from busker.model.types import Rank


class Resident:
    "A core-resident actor"
    # https://streamkap.com/resources-and-guides/streaming-api-design-patterns

    # Shared among subclasses within the same thread
    shared = contextvars.ContextVar("shared")
    executor = ThreadPoolExecutor()


class Engine(Resident):

    ignored_words = ("a", "an", "any", "her", "his", "my", "some", "the", "their")
    global_modules = dict(
        calendar=calendar, cmath=cmath, copy=copy,
        decimal=decimal, fractions=fractions,
        logging=logging, math=math, platform=platform,
        random=random, re=re, statistics=statistics,
        time=time, textwrap=textwrap, uuid=uuid,
        warnings=warnings, zoneinfo=zoneinfo,
        Exclamation=Exclamation, Note=Note, Rank=Rank,
    )

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

    Cue = namedtuple(
        "Cue",
        ["text", "html5", "rank", "clip", "lines", "words", "role", "details", "directives", "mode", "parameters", "fragments", "items"],
        defaults= (0, ) + (None,) * 9,
    )

    @classmethod
    def build(cls, *lenses, path: pathlib.Path, **kwargs) -> Engine:
        logger = logging.getLogger(cls.__name__)
        adaptor = Multipart(
            factory={dict: UserDict, list: UserList, str: UserString, "marking": Marker}
        )
        journal = Journal(adaptor, uri=path)
        journal.attach(*lenses)
        for event in journal.scan(**kwargs):
            logger.debug(event)
        engine = cls(journal)
        return engine.run()

    def __init__(self, journal: Journal = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.queues = (queue.Queue(maxsize=1), queue.Queue())
        self.scene = queue.PriorityQueue()
        self.journal = journal
        self.future = None
        self.listen = True
        self.mechanism = Mechanism()
        self.turn = 0
        self.clip = 0
        self.cues = []
        # TODO: Need a buffer so most recent contents can be reviewed.
        # TODO: Make Engine the owner of notes/comments/issues related to play

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

    def __call__(self, timeout=0.2, limit=sys.maxsize, **kwargs):
        "Engine execution assumes threaded concurrency"
        if not self.validate_journal():
            return

        while self.listen and self.turn < limit:
            try:
                text = self.queues[0].get(block=True, timeout=timeout)
            except queue.Empty:
                time.sleep(0)
                continue

            marking = self.journal.marking
            for marker in reversed(marking.values()):
                events = self.journal.events(marker.mark)
                actions = dict(help=self.do_help)
                actions.update(self.journal.actions(marker.mark, filter_context=marker))
                matches = self.match_text_to_phrases(text, actions)

                try:
                    self.logger.debug(f"Selecting first of matches {matches}")
                    element, kwargs = actions[matches[0]]
                    self.logger.debug(f"Map to {element.parent.path}: {kwargs=} {element=}")
                except IndexError:
                    self.logger.debug(f"No match for text '{text}'")
                    # TODO: Call unknown
                    pass
                except TypeError:
                    # The action is a local method
                    fn = actions[matches[0]]
                    try:
                        fn(text, marker=marker, marking=marking)
                    except Exclamation as report:
                        self.logger.info(report)
                    except Exception as err:
                        self.logger.warning(err)
                        self.logger.debug(err, exc_info=True)
                else:
                    bisect.insort_right(events, element, key=operator.attrgetter("rank"))

                # Activate pre-dialogue handlers
                for element in itertools.takewhile(lambda el: el.rank < Rank.DIALOGUE, events):
                    self.execute_handler(element, marker, **kwargs)

                # Insert content
                context = dict(self.journal.context(marker.mark), marker=marker)
                for text in self.journal.content(marker.mark):
                    self.insert_text(text, context=context, marker=marker)

                # Activate post-dialogue handlers
                for element in itertools.dropwhile(lambda el: el.rank < Rank.DIALOGUE, events):
                    self.execute_handler(element, marker, **kwargs)

            for cue in self.play_scene(self.scene):
                self.queues[1].put(cue, block=False)
                self.cues.append(cue)

            self.queues[0].task_done()
            self.turn += 1

    def validate_journal(self) -> bool:
        if not self.journal.marking:
            self.logger.warning(f"Journal has no marking")
            for path, values in self.journal.adaptor.data.items():
                self.logger.debug(f"FRAME at path {path}:")
                for item in values:
                    self.logger.debug(item)
            return False

        marker = next(iter(self.journal.marking.values()))
        try:
            _ = self.journal.actions(marker.mark)
        except AttributeError as err:
            self.logger.warning("Journal does not support action syntax")
            self.logger.debug(err, exc_info=True)
            return False

        return True

    def match_text_to_phrases(self, text: str, phrases: list[str], precision=0.95):
        return difflib.get_close_matches(text, phrases, cutoff=precision)

    def insert_text(self, text: str, rank: int = Rank.DIALOGUE, context: dict = None, marker: Marker = None):
        """Back-end method for use by handlers."""
        if context is None:
            cue_strs = [text]
        else:
            cue_strs = [
                self.mechanism.fix(cue_str, context)
                for cue_str in self.mechanism.split_cues(text)
                if all(self.mechanism.verdict(cue_str, context))
            ]

        for n, cue_str in enumerate(cue_strs):
            cue_str = textwrap.dedent(cue_str).lstrip()
            if marker is not None:
                cue_str = self.mechanism.rotate_cue(cue_str, marker=marker)

            self.clip += 1
            self.scene.put(Note(cue_str, rank=rank, clip=self.clip))

    def execute_handler(self, element: Element, marker: Marker, **kwargs):
        path = marker.mark
        context = self.journal.context(path)
        code = compile(element.handler, format(path), mode="exec")
        l = dict(kwargs, engine=self, context=context, marker=marker)
        # TODO: Configure globals
        try:
            exec(code, locals=l, globals=self.global_modules)
        except Exclamation as report:
            self.logger.info(report)
        except Exception as err:
            self.logger.warning(err, exc_info=True)

    def play_scene(self, scene: queue.Queue) -> Generator[Cue]:
        """Consume the contents of a scene, and generate cues for output."""
        while not scene.empty():
            try:
                item = scene.get(block=False)
                if not item.text.startswith("<"):
                    text = f"<> {item.text}"
                else:
                    text = item.text

                html5 = self.mechanism.processor.loads(text)
                yield from (
                    self.Cue(
                        item.text, html5, item.rank, item.clip,
                        **{k: v.copy() if hasattr(v, "copy") else v for k, v in cue.items()}
                    )
                    for cue in self.mechanism.processor.cues
                )
            except IndexError:
                # Empty cues
                pass
            except (queue.Empty, queue.Full):
                # TODO: Roll back?
                pass

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

    def do_help(self, *args, marker=None, **kwargs):
        self.logger.info(f"No help from {marker}!")
