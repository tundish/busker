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
from collections import UserDict
from collections import UserList
from collections import UserString
from collections.abc import Callable
import inspect
import logging
import pathlib
import re
import sys
import time

from spiki.speechmark import SpeechMark

from busker.engine.base import Engine
from busker.model.journal import Journal
from busker.model.multipart import Multipart

# <@0> xxx  # Route to engine index 0
# <> xxx    # Route to console
# xxxx      # Route to current engine
#
# Request actions, if none, then call `unknown` method.


class Console:
    intro = "Type '<> help' for more instructions.\n"
    prompt = "> "
    journal_lenses = [
        "busker.model.search:Search",
        "busker.model.syntax:Syntax",
        "busker.model.travel:Travel",
    ]
    plugin_classes = [
        "busker.engine.base:Engine",
    ]


    def __init__(self, args: argparse.Namespace, *lenses):
        self.logger = logging.getLogger("console")
        self.args = args
        self.parser = SpeechMark()
        self.streams = (sys.stdin, sys.stdout, sys.stderr)
        self.engines = []
        self.index = None

        try:
            self.engines.append(self.build_engine(*lenses, path=args.input))
            self.index = len(self.engines) - 1
        except IndexError as err:
            self.logger.warning(f"Error building engine from {args.input}")
            self.logger.debug(err, exc_info=True)

    @staticmethod
    def one_cue_per_line(text: str) -> str:
        return "\n".join(i.strip() for i in text.split(";"))

    @staticmethod
    def build_engine(*args, path: pathlib.Path, **kwargs) -> Engine:
        adaptor = Multipart(factory={dict: UserDict, list: UserList, str: UserString})
        journal = Journal(adaptor, uri=path)
        journal.attach(*args)
        journal.scan(**kwargs)
        engine = Engine(journal)
        return engine.run()

    def cmdloop(self, **kwargs):
        print(self.intro, file=self.streams[2])
        n = 0
        loop = True
        while loop:
            line = input(self.prompt)
            text = self.one_cue_per_line(line)
            self.parser.loads(text)

            cues = self.parser.cues
            if not cues:
                words = re.split(r"\W+", line)
                cues = [dict(role=str(self.index), words=words)]

            for cue in cues:
                print(f"{cue=}")
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
                        engine.queues[0].put(cmd, block=True, timeout=2)
                    except:
                        pass

                else:
                    print(f"Processing locally...", file=self.streams[2])
                    if not self.handle_cue(**cue):
                        loop = False
                        break

        self.logger.info("Closing down...")
        for engine in self.engines:
            engine.listen = False
            time.sleep(0)
        return

    def handle_cue(self, words: list, mode: str = "", parameters: dict = {}, directives: list = [], **kwargs):
        self.logger.info(words)
        try:
            method_name = "do_{0}".format(words[0])
            method = getattr(self, method_name)
            return method(*words[1:], **parameters)
        except (IndexError,):
            self.logger.info(words)
            return True

    def do_help(self, *args, **kwargs):
        "Show help"
        methods = {
            k: v
            for k in dir(self)
            if k.startswith("do_") and isinstance((v := getattr(self, k)), Callable)
        }
        for arg in args:
            try:
                fn = methods[f"do_{arg}"]
                print(arg, "-" * len(arg), sep="\n", file=self.streams[2])
                print(inspect.getdoc(fn), file=self.streams[2])
            except KeyError:
                continue
        if not args:
            print("Commands", "-" * 8, sep="\n", file=self.streams[2])
            print(*(f"+ {i[3:]}" for i in methods), sep="\n", file=self.streams[2])
        return True

    def do_quit(self, *args, **kwargs):
        "Quit the program"
        return False


def main(args):
    console = Console(args)
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
        "--debug", action="store_true", default=False,
        help=f"Display debug logs"
    )
    return rv


def run():
    p = parser()
    args = p.parse_args()
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        format="{asctime}| {levelname:>8}| {name:<18} | {message}",
        datefmt="",
        style="{",
        stream=sys.stderr,
        level=level,
    )
    rv = main(args)
    sys.exit(rv)


if __name__ == "__main__":
    run()
