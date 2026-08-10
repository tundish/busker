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

import pathlib
import unittest
import sys

from busker.runner import Discovery
from busker.runner import Installation
from busker.runner import Server
from busker.types import ExecutionEnvironment


class InstallationTests(unittest.TestCase):

    def test_pip_command_args(self):
        exenv = ExecutionEnvironment(
            "/home/user/src/busker/busker_ejdaibaf_venv",
            "/home/user/src/busker/busker_ejdaibaf_venv/bin/python",
        )
        distribution = "/home/user/src/busker/dist/busker-0.5.0.tar.gz"
        args = Installation.pip_command_args(
            interpreter=exenv.interpreter,
            distribution=distribution,
            update=True,
        )
        self.assertTrue(args)
        self.assertTrue(all(isinstance(i, str) for i in args), args)


class DiscoveryTests(unittest.TestCase):

    entry_points = [
        "hypercorn",
        "pip",
        "pip3",
        "pip3.10",
        "wheel",
    ]

    def test_filter(self):
        self.assertFalse(Discovery.filter_entry_points(self.entry_points))
        self.assertEqual(Discovery.filter_entry_points(self.entry_points + ["busker-cli"]), ["busker-cli"])

    def test_sorting(self):
        entry_points = self.entry_points + ["rotu-server"]
        values = Discovery.sort_entry_points(entry_points, like="rotu-")
        self.assertEqual(len(values), len(entry_points))
        self.assertEqual(values[0], entry_points[-1], values)


class ServerTests(unittest.TestCase):

    def test_command(self):
        if "win" in sys.platform.lower():
            self.assertEqual(
                Server.args(pathlib.Path("C:\\Program Files"), "story-server", "127.0.0.1", 8080),
                ["C:\\Program Files\\story-server", "--host", "127.0.0.1", "--port", "8080"]
            )
        else:
            self.assertEqual(
                Server.args(pathlib.Path("/usr/local/bin"), "story-server", "127.0.0.1", 8080),
                ["/usr/local/bin/story-server", "--host", "127.0.0.1", "--port", "8080"]
            )
