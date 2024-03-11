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
import textwrap
from types import SimpleNamespace

from busker.scraper import Scraper


class ScraperTests(unittest.TestCase):

    fixtures = SimpleNamespace(
        Home=textwrap.dedent("""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="ie=edge">
        <link rel="stylesheet" href="/static/basics.css" />
        <link rel="stylesheet" href="/static/layout.css" />
        <link rel="stylesheet" href="/static/object.css" />
        </head>
        <body>
        <form role="form" action="/sessions" method="POST" name="ballad-form-start">
        <button action="submit">Begin</button>
        </form>
        </body>
        </html>
        """),
    )

    def test_find_session_begin(self):
        scraper = Scraper()
        body_re = scraper.tag_matcher("body")
        match = body_re.search(self.fixtures.Home)
        rv = scraper.find_forms(match[0])
        self.fail(rv)
