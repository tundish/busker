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


"""
This utility checks scenes for mistakes.

Usage:

    python -m utils.snoop scenes/*

"""

import argparse
from collections import namedtuple
import pathlib
import pprint
import string
import sys

from busker.proofer import Proofer
from busker.utils.graph import load_rules


def main(args):
    """
    ".scene.toml": Scene,
    ".stage.toml": Staging,
    """
    assert all(i.is_dir() for i in args.input)
    scene_paths = [path for i in args.input for path in i.glob("*.scene.toml")]
    stage_paths = [path for i in args.input for path in i.glob("*.stage.toml")]
    print(f"{scene_paths=}", file=sys.stderr)
    print(f"{stage_paths=}", file=sys.stderr)

    for scene_path in scene_paths:
        formatter = string.Formatter()
        text = scene_path.read_text()
        for n, line in enumerate(text.splitlines()):
            print(line)

    data = list(load_rules(*stage_paths))
    stager = Stager(rules=data)
    snapshot = stager.snapshot
    pprint.pprint(snapshot, sort_dicts=False, stream=sys.stderr)
    return 0


def parser():
    rv = argparse.ArgumentParser(__doc__)
    rv.add_argument(
        "input", nargs="+", type=pathlib.Path,
        help="Specify input directories."
    )
    return rv


def run():
    p = parser()
    args = p.parse_args()
    rv = main(args)
    sys.exit(rv)


if __name__ == "__main__":
    run()
