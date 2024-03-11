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
import sys

import httpx

from balladeer import discover_assets

import busker


def main(args):
    # assets = discover_assets(args.source, "")
    print(f"Busker {busker.__version__}", file=sys.stderr)
    page = httpx.get(args.url)
    print(f"{page.text}", file=sys.stdout)
    print("Done.", file=sys.stderr)
    return 0

def parser():
    rv = argparse.ArgumentParser()
    rv.add_argument(
        "--url", default="http://localhost:8080",
        help="Set url path to begin session."
    )
    return rv

def run():
    p = parser()
    args = p.parse_args()
    rv = main(args)
    sys.exit(rv)


if __name__ == "__main__":
    run()
