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
        <button type="submit">Begin</button>
        </form>
        </body>
        </html>
        """),
        Session=textwrap.dedent("""
        <!DOCTYPE html>
        <html>
        <head>
        <title>Story</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="ie=edge">
        <link rel="stylesheet" href="/static/basics.css" />
        <link rel="stylesheet" href="/static/layout.css" />
        <link rel="stylesheet" href="/static/object.css" />
        <style type="text/css">
        :root {
        --ballad-ink-gravity: hsl(282.86, 100%, 14.12%);
        --ballad-ink-shadows: hsl(203.33, 96.92%, 8.75%);
        --ballad-ink-lolight: hsl(203.39, 96.72%, 11.96%);
        --ballad-ink-midtone: hsl(203.39, 96.72%, 31.96%);
        --ballad-ink-hilight: hsl(203.06, 97.3%, 56.47%);
        --ballad-ink-washout: hsl(50.00, 0%, 100%);
        --ballad-ink-glamour: hsl(66.77, 96.92%, 72.75%);
        }
        </style>
        </head>
        <body>
        <main>
        <div class="ballad cue">
        <blockquote cite="&lt;GOAL&gt;">
        <cite data-role="GOAL" data-entity="goal_00a"
        style="animation-delay: 1.00s; animation-duration: 0.10s">goal_00a</cite>
        <p style="animation-delay: 1.00s; animation-duration: 0.30s">I am goal_00a.</p>
        </blockquote>
        </div>
        <div class="ballad cue">
        <blockquote cite="&lt;GOAL.branching&gt;">
        <cite data-role="GOAL" data-entity="goal_00a"
        data-directives=".branching" style="animation-delay: 2.30s; animation-duration: 0.10s">goal_00a</cite>
        <p style="animation-delay: 2.30s; animation-duration: 0.50s">Do you want to figure out where you are?</p>
        <ol>
        <li id="1"><p style="animation-delay: 3.80s; animation-duration: 0.10s">Yes</p></li>
        <li id="2"><p style="animation-delay: 4.90s; animation-duration: 0.10s">No</p></li>
        </ol>
        </blockquote>
        </div>
        </main>

        <datalist id="ballad-command-form-input-list">
        <option value="1"></option>
        <option value="2"></option>
        <option value="i"></option>
        <option value="info"></option>
        <option value="no"></option>
        <option value="yes"></option>
        </datalist>

        <div id="ballad-zone-inputs" class="ballad zone">

        <form role="form"
        action="http://localhost:8080/session/79453e2d-d200-44f5-84b1-7dde4f25fc90/command"
        method="post" name="ballad-command-form">
        <fieldset>
        <label for="ballad-command-form-input-text" id="ballad-command-form-input-text-label">&gt;</label>

        <input
        name="ballad-command-form-input-text"
        placeholder=""
        pattern="[\w ]+"
        autofocus="autofocus"
        type="text"
        title="Enter a command, or type 'help' for a list of options."
        list="ballad-command-form-input-list"
        />
        <button type="submit">Enter</button>
        </fieldset>
        </form>

        </div>
        </body>
        </html>
        """),
        blockquote=textwrap.dedent("""
        <blockquote cite="&lt;STAFF.approaching.proposing@TABLE,GUEST:mutters/male/rhubarb?pause=0.3&amp;dwell=0.1#3&gt;">
        <cite data-role="STAFF" data-directives=".approaching.proposing@TABLE,GUEST" data-mode=":mutters/male/rhubarb" data-parameters="?pause=0.3&amp;dwell=0.1" data-fragments="#3">STAFF</cite>
        <p>

        What would you like sir? We have some very good fish today.
        </p>
        <ol>
        <li id="1"><p>
        Order the Beef Wellington
        </p></li>
        <li id="2"><p>
        Go for the Cottage Pie
        </p></li>
        <li id="3"><p>
        Try the Dover Sole
        </p></li>
        </ol>
        </blockquote
        """),
    )

    def test_find_home_begin(self):
        scraper = Scraper()
        body_re = scraper.tag_matcher("body")
        match = body_re.search(self.fixtures.Home)
        rv = scraper.find_forms(match[0])
        self.assertEqual(len(rv), 1)

    def test_find_session_command(self):
        scraper = Scraper()
        body_re = scraper.tag_matcher("body")
        match = body_re.search(self.fixtures.Session)
        rv = scraper.find_forms(match[0])
        self.assertEqual(len(rv), 1)

    def test_find_title(self):
        scraper = Scraper()
        for n, text in enumerate((self.fixtures.Home, self.fixtures.Session)):
            with self.subTest(n=n, text=text):
                title = scraper.find_title(text)
                if n == 0:
                    self.assertIsNone(title)
                else:
                    self.assertEqual(title, "Story", title)

    def test_find_blocks(self):
        scraper = Scraper()
        blocks = scraper.find_blocks(self.fixtures.Session)
        self.assertEqual(len(blocks), 2)
        self.assertTrue(all(i.startswith("<blockquote") for i in blocks))
        self.assertTrue(all(i.endswith("blockquote>") for i in blocks))

    def test_get_forms_from_session(self):
        scraper = Scraper()
        for n, text in enumerate((self.fixtures.Home, self.fixtures.Session)):
            with self.subTest(n=n, text=text):
                body_re = scraper.tag_matcher("body")
                match = body_re.search(text)
                form = next(scraper.get_forms(match[0]), None)
                self.assertTrue(form)
                if n == 0:
                    self.assertTrue(all(form._replace(inputs=True)), form)
                else:
                    self.assertTrue(all(form), form)
                    self.assertTrue(all(form.inputs))
                    self.assertTrue(all(i for i in form.inputs))
