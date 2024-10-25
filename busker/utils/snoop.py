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
#! /usr/bin/env python
# encoding: utf-8


"""
This utility checks scenes for mistakes.

Usage:

    python -m utils.snoop scenes/*/*.stage.toml

"""

import argparse
from collections.abc import Generator
import pathlib
import pprint
import sys

from busker.stager import Stager
from busker.utils.graph import load_rules


def main(args):
    data = list(load_rules(*args.input))
    stager = Stager(rules=data)
    snapshot = stager.snapshot
    pprint.pprint(snapshot, sort_dicts=False, stream=sys.stderr)
    return 0


def parser():
    rv = argparse.ArgumentParser(__doc__)
    rv.add_argument(
        "input", nargs="+", type=pathlib.Path,
        help="Set input file."
    )
    return rv


def run():
    p = parser()
    args = p.parse_args()
    rv = main(args)
    sys.exit(rv)


if __name__ == "__main__":
    run()
