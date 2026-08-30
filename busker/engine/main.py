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
import cmd
import logging
import pathlib
import readline
import sys

from busker.engine.base import Engine
from busker.model.journal import Journal


class Console(cmd.Cmd):
    intro = "Type 'help' for more instructions."
    prompt = "> "

    @staticmethod
    def parse(line: str):
        for word in line.split():
            word = word.strip()
            if not word: continue

            if word.isdigit():
                yield float(word)
            else:
                yield word

    def __init__(self, args: argparse.Namespace):
        super().__init__(self)
        self.logger = logging.getLogger("console")
        self.args = args
        self.engine = Engine()

    def preloop(self):
        self.onecmd("file feed")

    def precmd(self, line):
        self.logger.debug(f"{line=}")
        return line

    def default(self, line: str):
        cmds = [i.strip() for i in line.split(";")]
        self.engine.put(*cmds)
        self.stdout.write("")

    def do_file(self, line: str):
        "Read or feed the file"
        cmd = list(self.parse(line))
        if len(cmd) == 0:
            self.logger.info(f"File input: {self.args.input}")
            return
        elif cmd[0].lower() in ("feed", "read"):
            text = self.args.input.read_text()
            self.logger.debug(f"\n{text}")
        else:
            self.logger.warning(f"Bad syntax: {cmd}")

        if cmd[0].lower() == "feed":
            try:
                self.engine.rht = Journal.scan(text)
                self.logger.info(f"Engine feed: {self.args.input}")
                self.logger.debug(f"\n{self.engine.rht.doc}")
            except Exception as err:
                self.logger.error(err, exc_info=True)

    def do_path(self, line: str):
        "View paths"
        cmd = list(self.parse(line))
        try:
            lookup = {format(k): v for k, v in self.engine.rht.doc.data.items()}
        except AttributeError:
            self.logger.error("'file feed' required.")
            return

        if len(cmd) == 0:
            self.logger.debug(self.engine.rht.doc.data)
            self.logger.info("\n".join(lookup))
        else:
            pass
            return

    def do_quit(self, line: str):
        "Quit the program"
        return True


plugin_classes = [
    "busker.engine.base:Engine",
]


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
        help=f"Specify plugin list {plugin_classes}"
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
