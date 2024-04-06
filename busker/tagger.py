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

import html.parser
import tkinter as tk
from tkinter import font as tkf


class Tagger(html.parser.HTMLParser):
    """
    Tags support the following configuration options:
        * background
        * bgstipple
        * borderwidth
        * elide
        * fgstipple
        * font
        * foreground
        * justify
        * lmargin1
        * lmargin2
        * offset
        * overstrike
        * relief
        * rmargin
        * spacing1
        * spacing2
        * spacing3
        * tabs
        * tabstyle
        * underline
        * wrap.

    """

    @staticmethod
    def configure(widget: tk.Text):
        cite_font = tkf.nametofont("TkFixedFont").copy()
        cite_font.config(weight="bold")

        widget.tag_configure("blockquote", tabs=("12p", "24p", "12p", tk.NUMERIC, "6p"))
        widget.tag_configure(
            "cue", spacing1="6p", spacing3="6p",
            foreground="#BCBCBC", background="#0E0E0E",
            font="TkFixedFont"
        )
        widget.tag_configure("cite", foreground="#1C1C1C", spacing1="6p", spacing3="6p", font=cite_font)
        widget.tag_configure("p", spacing1="6p", spacing3="6p", font="TkTextFont")
        widget.tag_configure("li", spacing1="3p", spacing3="3p")
        return widget

    def __init__(self, widget, convert_charrefs=True):
        super().__init__(convert_charrefs=convert_charrefs)
        self.widget = widget
        self.tags = []

    @property
    def indent(self):
        return "\t" * (len(self.tags) - self.tags.count("div"))
        return "\t" * (self.tags.count("blockquote") + self.tags.count("p") + self.tags.count("li"))

    def handle_starttag(self, tag: str, attrs: dict):
        self.tags.append(tag)
        attribs = dict(attrs)
        if tag == "div":
            return
        elif tag == "blockquote":
            self.widget.insert(tk.END, "\n", self.tags)
            self.widget.insert(tk.END, f"{self.indent}{attribs['cite']}\n", self.tags + ["cue"])
        elif tag in ("ol", "ul"):
            pass
        elif tag == "li" and attrs:
            self.widget.insert(tk.END, f"{self.indent}{attribs['id']}.", self.tags)

    def handle_endtag(self, tag: str):
        if self.tags and self.tags[-1] == tag:
            self.tags.pop(-1)

    def handle_data(self, text:str):
        text = text.strip()
        if not text: return
        print(f"{text=} {len(self.indent)=}")
        indent = "\t" * (len(self.indent) - self.tags.count("li"))

        self.widget.insert(tk.END, f"{indent}{text}\n", self.tags)
        self.widget.see(tk.END)
