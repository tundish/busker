#!/usr/bin/env python
#   encoding: utf-8

# Copyright (C) 2026 D E Haynes
# This file is part of busker.

# Busker is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# Busker is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with busker.
# If not, see <https://www.gnu.org/licenses/>.

from collections import UserDict
from collections import UserList
from collections import UserString
import importlib.resources
import queue
import time
import unittest

from busker.engine.engine import Engine
from busker.engine.marker import Marker
from busker.model.journal import Journal
from busker.model.descent import Descent
from busker.model.multipart import Multipart
from busker.model.search import Search
from busker.model.syntax import Syntax
from busker.model.travel import Travel


class EngineTests(unittest.TestCase):

    def setUp(self):
        with importlib.resources.path("busker.data", "demo/cloak_of_harkness.rht") as path:
            self.assertTrue(path.exists(), path)
            lenses = (Descent, Search, Syntax, Travel)
            self.engine = Engine.build(*lenses, path=path)

    def tearDown(self):
        self.engine.listen = False
        time.sleep(0)

    def test_world_marker(self):
        self.engine.queues[0].put("go north")
        self.engine.queues[0].join()
        scene = []
        while True:
            try:
                scene.append(self.engine.queues[1].get(block=False))
            except queue.Empty:
                break
        print(*scene, sep="\n")

