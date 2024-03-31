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

import unittest

from busker.runner import Discovery
from busker.runner import Installation
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

    data = [
        "pip",
        "pip3",
        "pip3.10",
    ]

    def test_filter(self):
        self.assertFalse(Discovery.filter_endpoints(self.data))
        self.assertEqual(Discovery.filter_endpoints(self.data + ["busker-cli"]), ["busker-cli"])
