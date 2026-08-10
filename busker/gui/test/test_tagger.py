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
import tkinter as tk
import unittest

from busker.tagger import Tagger


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

    def test_tagger_catches_div(self):
        widget = tk.Text()
        tagger = Tagger(widget)
        tagger.feed(self.html[0])
        self.assertEqual(tagger.tags, ["div"])

    def test_tagger_text(self):
        widget = tk.Text()
        tagger = Tagger(widget)
        tagger.feed(self.html[0])
        text = widget.get(1.0, tk.END)
        self.assertEqual(len(text.splitlines()), 11)

    def test_tagger_tags(self):
        widget = Tagger.configure(tk.Text())
        tagger = Tagger(widget)
        tagger.feed(self.html[0])
        text = widget.get(1.0, tk.END)
        tags = ("blockquote", "cite", "p", "ol", "li")
        self.assertLessEqual(set(tags), set(widget.tag_names()))


if __name__ == "__main__":
    from tkinter import font
    root = tk.Tk()
    print(font.families(), sep="\n")
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    widget = Tagger.configure(tk.Text(root))
    widget.grid(sticky="nsew")
    tagger = Tagger(widget)
    tagger.feed(TaggerTests.html[0])
    widget["state"] = tk.DISABLED
    root.mainloop()
