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

import datetime
import pathlib
import platform
import textwrap
from types import SimpleNamespace
import tomllib
import unittest

from busker.executive import Executive


class ExecutiveTests(unittest.TestCase):

    data = SimpleNamespace(
        pyvenv_cfg = textwrap.dedent("""
        home = /usr/local/bin
        include-system-site-packages = true
        version = 3.11.2
        executable = /usr/local/bin/python3.11
        command = /home/user/py3.11-dev/bin/python -m venv --copies --system-site-packages --upgrade-deps /home/user/src/busker/busker_t9p2rtkw_venv
        """),
    )

    def test_venv_dict(self):
        rv = dict(Executive.venv_data(self.data.pyvenv_cfg))
        self.assertIsInstance(rv, dict)
        self.assertEqual(len(rv), 5)
        self.assertEqual(rv.get("home"), "/usr/local/bin")

    def test_venv_dict_empty(self):
        rv = dict(Executive.venv_data(""))
        self.assertIsInstance(rv, dict)
        self.assertFalse(rv)

    def test_venv_exe(self):
        data = dict(Executive.venv_data(self.data.pyvenv_cfg))
        path = pathlib.Path(data.get("command", "").split()[-1])
        rv = Executive.venv_exe(path, **data)
        self.assertIsInstance(rv, pathlib.Path)
        self.assertEqual(rv.name, "python3.11")
        if platform.system().lower() == "windows":
            self.assertEqual(rv.parent.name, "Scripts")
        else:
            self.assertEqual(rv.parent.name, "bin")
        self.assertEqual(rv.parent.parent.name, "busker_t9p2rtkw_venv", rv)
