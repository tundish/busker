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

    python -m utils.proofread project/scripts

"""

import argparse
from collections import namedtuple
import pathlib
import pprint
import string
import sys

from busker.stager import Stager
from busker.proofer import Proofer
from busker.utils.graph import load_rules


def main(args):
    directories = [i for i in args.input if i.is_dir()]
    for path in args.input:
        if path not in directories:
            print(f"Skipping {path!s} (not a directory)")

    stage_scripts = [Proofer.read_script(path) for i in directories for path in i.glob("*.stage.toml")]

    for script in Proofer.check_stage(*stage_scripts):
        print(f"{script.path!s}\t{script.errors=}", file=sys.stderr)

    scene_paths = [path for i in directories for path in i.glob("*.scene.toml")]
    for path in scene_paths:
        script = Proofer.read_script(path)
        script = Proofer.check_scene(script)
        print(f"{script.path!s}\t{script.errors=}", file=sys.stderr)

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
