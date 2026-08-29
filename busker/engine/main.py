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
import sys


class Console(cmd.Cmd):

    def __init__(self):
        self.logger = logging.getLogger("engine")
        super().__init__(self)

    def precmd(self, line):
        self.logger.info(f"{line=}")
        return line


plugin_classes = [
    "busker.engine.base:Engine",
]


def main(args):
    console = Console()
    console.cmdloop(intro="Type help for more instructions.")
    return 0


def parser():
    rv = argparse.ArgumentParser(usage=__doc__, fromfile_prefix_chars="=")
    rv.convert_arg_line_to_args = lambda x: x.split()
    rv.add_argument(
        "--input",
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
