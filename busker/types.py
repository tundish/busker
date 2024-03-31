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

from collections import namedtuple
import dataclasses
import enum
import multiprocessing
import multiprocessing.managers
import multiprocessing.pool
import pathlib


Completion = namedtuple("Completion", ["runner", "exenv", "data"], defaults=[None])


class Host(enum.Enum):

    IPV4_LOOPBACK = "127.0.0.1"
    IPV4_NET_HOST = "0.0.0.0"
    IPV6_LOOPBACK = "::1"
    IPV6_NET_HOST = "::"


@dataclasses.dataclass
class ExecutionEnvironment:
    location: pathlib.Path
    interpreter: pathlib.Path = None
    config: dict = None
    pool: multiprocessing.pool.Pool = None
    manager: multiprocessing.managers.SyncManager = None
    queue: multiprocessing.Queue = None
