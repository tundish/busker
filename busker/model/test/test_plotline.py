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
import textwrap
import unittest

from busker.model.multipart import Multipart


class PlotlineTests(unittest.TestCase):

    def test_types(self):
        doc = Multipart()
        doc.data[()].append(UserDict(a=1, b=2, c=3))
        doc.data[(0,)].append(
            textwrap.dedent("""
            Once upon a time...
            """)
        )
        doc.data[(1,)].append(
            textwrap.dedent("""
            There was a little sausage called Baldrick.
            """)
        )
        doc.data[(1,)].append(UserDict(a="a", b=1))
        doc.data[(2,)].append(
            textwrap.dedent("""
            And he lived happily ever after.
            """)
        )
        rv = str(doc)
        self.fail(rv)

