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

from busker.gui import Zone


class ZoneTests(unittest.TestCase):

    def tearDown(self):
        Zone.registry.clear()

    def test_registry(self):

        class A(Zone):
            pass

        self.assertNotIn("A", Zone.registry)
        a = A(None)

        self.assertIn("A", Zone.registry)
        self.assertIsInstance(Zone.registry["A"], list)
