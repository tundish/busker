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

import textwrap
import unittest


class TaggerTests(unittest.TestCase):

    html = [
        textwrap.dedent("""
        <blockquote cite="&lt;GOAL&gt;">
        <cite data-role="GOAL" data-entity="goal_00a" style="animation-delay: 1.00s; animation-duration: 0.10s">goal_00a</cite>
        <p style="animation-delay: 1.00s; animation-duration: 0.30s">I am goal_00a.</p>
        </blockquote>
        </div>
        <div class="ballad cue">
        <blockquote cite="&lt;GOAL.branching&gt;">
        <cite data-role="GOAL" data-entity="goal_00a" data-directives=".branching" style="animation-delay: 2.30s; animation-duration: 0.10s">goal_00a</cite>
        <p style="animation-delay: 2.30s; animation-duration: 0.50s">Do you want to figure out where you are?</p>
        <ol>
        <li id="1"><p style="animation-delay: 3.80s; animation-duration: 0.10s">Yes</p></li>
        <li id="2"><p style="animation-delay: 4.90s; animation-duration: 0.10s">No</p></li>
        </ol>
        </blockquote>
        """),
    ]

    def test_single_blockquote(self):
        print(self.html)
