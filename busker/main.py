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

import argparse
from collections.abc import Callable
import difflib
import inspect
import logging
import math
import pathlib
import pkgutil
import queue
import re
import sys
import time

try:
    import readline
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set editing-mode vi")
except ModuleNotFoundError:
    readline = None

from spiki.speechmark import SpeechMark

from busker.engine.engine import Engine

# <@0> xxx  # Route to engine index 0
# <> xxx    # Route to console
# xxxx      # Route to current engine
#
# Request actions, if none, then call `unknown` method.


class Console:
    intro = "Type '<> help' for more instructions.\n"
    prompt = "\n> "
    journal_lenses = [
        "busker.model.search:Search",
        "busker.model.syntax:Syntax",
        "busker.model.travel:Travel",
    ]
    plugin_classes = [
        "busker.engine.engine:Engine",
    ]
    delay_prompt = 0.1

    def __init__(self, args: argparse.Namespace, *lenses):
        self.logger = logging.getLogger("console")
        self.args = args
        self.parser = SpeechMark()
        self.streams = (sys.stdin, sys.stdout, sys.stderr)
        self.engines = []
        self.index = None

        try:
            self.engines.append(Engine.build(*lenses, path=args.input))
            self.index = len(self.engines) - 1
        except IndexError as err:
            self.logger.warning(f"Error building engine from {args.input}")
            self.logger.debug(err, exc_info=True)

    @staticmethod
    def one_cue_per_line(text: str) -> str:
        return "\n".join(i.strip() for i in text.split(";"))

    @property
    def methods(self):
        return {
            k: v
            for k in dir(self)
            if k.startswith("do_") and isinstance((v := getattr(self, k)), Callable)
        }

    def cmdloop(self, **kwargs):
        print(self.intro, file=self.streams[2])
        n = 0
        loop = True
        while loop:
            time.sleep(self.delay_prompt)
            line = input(self.prompt)
            text = self.one_cue_per_line(line)
            self.parser.loads(text)

            cues = self.parser.cues
            if not cues:
                words = re.split(r"\W+", line)
                cues = [dict(role=str(self.index), words=words)]

            for cue in cues:
                n += 1
                role = cue.get("role", None)
                cmd = " ".join(cue["words"])
                if role:
                    try:
                        index = int(role)
                        engine = self.engines[index]
                        self.index = index
                    except IndexError:
                        print(f"No Engine exists at index {index}.", file=self.streams[2])
                        print(f"Command {n} discarded: '{cmd}'.", file=self.streams[2])
                        continue
                    except ValueError:
                        print(f"Invalid index.", file=self.streams[2])
                        print(f"Command {n} discarded: '{cmd}'.", file=self.streams[2])
                        continue

                    try:
                        self.logger.debug(f"Submitting '{cmd}' to {engine}")
                        engine.queues[0].put(cmd, block=True, timeout=2)
                    except queue.Full:
                        # What now?
                        pass

                    self.logger.debug(f"Waiting for complete")
                    engine.queues[0].join()

                    while True:
                        try:
                            item = engine.queues[1].get(block=False)
                            print(item, file=self.streams[1])
                            self.streams[1].flush()
                        except queue.Empty:
                            break

                else:
                    self.logger.debug("Processing locally")
                    if not self.handle_local(**cue):
                        loop = False
                        break

        self.logger.info("Closing down...")
        for engine in self.engines:
            engine.listen = False
            time.sleep(0)
        return

    def handle_local(self, words: list, mode: str = "", parameters: dict = {}, directives: list = [], **kwargs):
        self.logger.debug(f"{words=}")
        try:
            pick = difflib.get_close_matches(f"do_{words[0]}", self.methods, n=1)
            method = getattr(self, pick[0])
            return method(*words[1:], **parameters)
        except (IndexError,) as err:
            print("No local handler for command '{0}'".format(" ".join(words)), file=self.streams[2])
            self.logger.debug(f"{words=}", exc_info=True)
            return True

    def do_help(self, *args, **kwargs):
        """
        Show help

        """
        for arg in args:
            try:
                fn = self.methods[f"do_{arg}"]
                print(arg, "-" * len(arg), sep="\n", file=self.streams[2])
                print(inspect.getdoc(fn), file=self.streams[2])
            except KeyError:
                continue
        if not args:
            print("Commands", "-" * 8, sep="\n", file=self.streams[2])
            print(*(f"+ {i[3:]}" for i in self.methods), sep="\n", file=self.streams[2])
        return True

    def do_list(self, *args, **kwargs):
        """
        List the currently running Engines

        """
        pad = round(math.log10(len(self.engines)) + 0.5) + 1
        if not args:
            print("Engines", "-" * 7, sep="\n", file=self.streams[2])
            print(*(f"{{0: >{pad}}}: {{1!r}}".format(n, i) for n, i in enumerate(self.engines)), sep="\n", file=self.streams[2])
        return True

    def do_quit(self, *args, **kwargs):
        """
        Quit the program

        """
        return False


def main(args):
    logger = logging.getLogger()
    lenses = []
    for spec in args.lens:
        lenses.append(pkgutil.resolve_name(spec))
        logger.info(f"Loaded lens {lenses[-1]}")
    console = Console(args, *lenses)
    console.cmdloop()
    return 0



def parser():
    rv = argparse.ArgumentParser(usage=__doc__, fromfile_prefix_chars="=")
    rv.convert_arg_line_to_args = lambda x: x.split()
    rv.add_argument(
        "input",
        type=pathlib.Path, default=None,
        help=f"Specify .rht file"
    )
    rv.add_argument(
        "--plugin", action="append",
        help=f"Specify plugin list {Console.plugin_classes}"
    )
    rv.add_argument(
        "--lens", action="append", default=(default := Console.journal_lenses),
        help=f"Specify lens list {default}"
    )
    rv.add_argument(
        "--debug", action="store_true", default=False,
        help=f"Display debug logs"
    )
    return rv


def run():
    p = parser()
    args = p.parse_args()
    level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(
        format="{levelname:>8}| {relativeCreated:>10,.0f} | {name:<18} | {message}",
        datefmt="",
        style="{",
        stream=sys.stderr,
        level=level,
    )
    rv = main(args)
    sys.exit(rv)


if __name__ == "__main__":
    run()
