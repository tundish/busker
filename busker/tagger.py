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


class Tagger(html.parser.HTMLParser):

    @staticmethod
    def configure(widget: tk.Text):
        widget.tag_configure("cite", background="yellow", font="TkFixedFont", relief="raised")
        return widget

    def __init__(self, widget, convert_charrefs=True):
        super().__init__(convert_charrefs=convert_charrefs)
        self.widget = widget
        self.tags = []

    def handle_starttag(self, tag: str, attrs: dict):
        self.tags.append(tag)

    def handle_endtag(self, tag: str):
        if self.tags[-1] == tag:
            self.tags.pop(-1)

    def handle_data(self, text:str):
        text = text.strip()
        if text:
            self.widget.insert(tk.END, f"{text}\n", self.tags)
            self.widget.see(tk.END)
