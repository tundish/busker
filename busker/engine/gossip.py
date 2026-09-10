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
import asyncio
import concurrent.futures
import logging
import pathlib
import queue
import sys


"""
Demo of multiple threads accessing the same Journal, eg:
    + A thread running an asyncio web stack
    + A continuous mapper / design rule checker
    + A backend text console
    + A sync / backup thread

Need to manage the write lock, etc.

"""

class LogBridge(logging.Handler):

    def __init__(self, log_queue: queue.Queue, level=logging.NOTSET, fmt=None, defaults=None):
        super().__init__(level=level)
        self.log_queue = log_queue
        fmt = fmt or "{asctime}| {levelname:>8}| {name:<18} | {message}",
        self.setFormatter(logging.Formatter(fmt=fmt, datefmt=None, style="{", validate=True, defaults=defaults))

    def emit(self, record):
        msg = self.formatter.format(record)
        self.log_queue.put(msg, block=False)

async with asyncio.TaskGroup() as tasks:

class Monk:

    def __init__(self, cmd_queue: asyncio.Queue() = None, msg_queue: asyncio.Queue() = None):
        self.cmd_queue = cmd_queue or asyncio.Queue()
        self.msg_queue = msg_queue or asyncio.Queue()


def start():
    pass


def main(args):
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
