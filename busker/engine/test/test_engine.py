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

import ast
from collections import UserDict
from collections import UserList
from collections import UserString
import importlib.resources
import logging
import platform
import textwrap
import unittest

from busker.engine.base import Engine
from busker.model.journal import Journal
from busker.model.multipart import Multipart
from busker.model.plotline import Plotline
from busker.model.types import Chain
from busker.model.types import Element
from busker.model.types import ElementType
from busker.model.types import Frame

from busker.model.test.test_plotline import PlotlineTests


class EngineTests(unittest.TestCase):

    def setUp(self):
        with importlib.resources.path("busker.data", "cloak_of_harkness.rht") as path:
            adapter = Multipart(factory={dict: UserDict, list: UserList, str: UserString})
            journal = Journal(adapter, uri=path)
            self.engine = Engine(journal)

    def test_world_marker(self):
        events = self.engine.put("go north")
        done = self.engine.step()
        self.fail(done)
