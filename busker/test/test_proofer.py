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
import tempfile
import unittest

from busker.proofer import Proofer


class ProoferTests(unittest.TestCase):

    def test_read_scenes_not_found(self):
        proofer = Proofer()
        with tempfile.TemporaryDirectory() as parent:
            path = pathlib.Path(parent).joinpath("null.scene.toml")
            scripts = list(proofer.read_scenes([path]))
        self.assertFalse(scripts)
