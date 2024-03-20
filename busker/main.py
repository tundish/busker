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

import argparse
import asyncio
from collections import Counter
import logging
import pathlib
import tempfile
import tomllib
from types import SimpleNamespace
import sys

import busker
import busker.gui
from busker.history import SharedHistory
from busker.scraper import Scraper
from busker.visitor import Visitor


defaults = SimpleNamespace(
    config=pathlib.Path("~/busker.toml").expanduser(),
)


def main(args):
    history = SharedHistory(log_name="busker")
    history.log(f"Busker {busker.__version__}")

    try:
        text = args.config.read_text()
        config = tomllib.loads(text)
    except FileNotFoundError:
        config = {}
    except tomllib.TOMLDecodeError as e:
        history.log(f"Error reading config file at {args.config}", level=logging.WARNING)
        history.log(f"{e!s}", level=logging.ERROR)
        return 2

    root = busker.gui.build(config)
    root.mainloop()
    return 0

    witness = Counter()

    n = 0
    while n < args.number:
        n += 1
        history.log(f"Run: {n:03d}")
        visitor = Visitor(args.url)
        while visitor.tactics:
            tactic = visitor.tactics.popleft()
            node = visitor(tactic)
            if node:
                history.log(f"Page: {node.title}")

        witness[visitor.turns] += 1

    history.log(f"{visitor.turns} done.")

    print(*visitor.toml_lines(visitor.history), sep="\n")
    print({k: witness[k] for k in sorted(witness.keys())})
    return 0


def parser(defaults):
    rv = argparse.ArgumentParser()

    setting_options = rv.add_argument_group("Settings")
    hosting_options = rv.add_argument_group("Hosting")
    playing_options = rv.add_argument_group("Playing")
    plugins_options = rv.add_argument_group("Plugins")

    setting_options.add_argument(
        "--config",
        type=pathlib.Path,
        default=defaults.config,
        help=f"Set a path to a configuration file [{defaults.config}].",
    )

    plugins_options.add_argument(
        "--url", default="http://localhost:8080",
        help="Set url path to begin session."
    )
    plugins_options.add_argument(
        "--number", type=int, default="64",
        help="Set the number of times to run the plugin."
    )
    return rv


def run():
    logging.basicConfig(
        format="{asctime}| {levelname:>8}| {name:<18} | {message}",
        datefmt="",
        style="{",
        stream=sys.stderr,
        level="INFO",
    )
    p = parser(defaults)
    args = p.parse_args()
    rv = main(args)
    sys.exit(rv)


if __name__ == "__main__":
    run()
