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

from collections import defaultdict
from collections import deque
import concurrent.futures
import enum
import logging
import pathlib
import tempfile
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from types import SimpleNamespace as Structure
import urllib.error
import urllib.parse
import venv

import busker
from busker.history import SharedHistory
from busker.runner import Runner
from busker.scraper import Scraper
from busker.zone import Zone
import busker.visitor


class Host(enum.Enum):

    IPV4_LOOPBACK = "127.0.0.1"
    IPV4_NET_HOST = "0.0.0.0"
    IPV6_LOOPBACK = "::1"
    IPV6_NET_HOST = "::"


class InfoZone(Zone):

    def __init__(self, parent, name="", **kwargs):
        super().__init__(parent, name=name, **kwargs)
        self.scraper = Scraper()
        self.reader = None

    def build(self, frame: ttk.Frame):
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=2)
        frame.columnconfigure(2, weight=1)
        frame.columnconfigure(3, weight=4)
        yield "label", self.grid(ttk.Label(frame, text="URL"), row=0, column=0, padx=(1, 1) )
        yield "entry", self.grid(ttk.Entry(frame, justify=tk.LEFT), row=0, column=1, padx=(1, 1), sticky=tk.W + tk.E)
        yield "button", self.grid(
            tk.Button(frame, text="Connect", command=self.on_connect),
            row=0, column=2, padx=(10, 10), sticky=tk.E
        )
        yield "label", self.grid(ttk.Label(frame, text="No connection to host"), row=0, column=3, padx=(1, 1))

    def on_connect(self):
        host = self.controls.entry[0].get()
        url = urllib.parse.urljoin(host, "about")
        self.reader = busker.visitor.Read(url=url)
        info = self.controls.label[1]
        try:
            node = self.reader.run(self.scraper)
        except (ValueError, urllib.error.URLError) as e:
            info.configure(text="No connection to host")
            self.log(f"{e!s}", level=logging.WARNING)
            return

        info.configure(text=node.text.strip())


class InteractiveZone(Zone):

    def build(self, frame: ttk.Frame):
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        text_widget = tk.Text(frame, height=6)
        scroll_bar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scroll_bar.set)
        yield "text", self.grid(text_widget, row=0, column=0, columnspan=2, padx=(10, 10), sticky=tk.W + tk.N + tk.E + tk.S)
        yield "scroll", self.grid(scroll_bar, row=0, column=2, pady=(10, 10), sticky=tk.N + tk.S)

        combo_box = ttk.Combobox(frame, justify=tk.LEFT)
        yield "entry", self.grid(combo_box, row=1, column=0, padx=(10, 10), sticky=tk.W + tk.E)

        yield "button", self.grid(
            tk.Button(frame, text="Launch", command=self.on_launch),
            row=1, column=1,  columnspan=2, padx=(10, 10), sticky=tk.E
        )
        # TODO: assist checkbox

    def on_launch(self):
        host = self.controls.entry[0].get()
        url = urllib.parse.urljoin(host, "about")
        self.reader = busker.visitor.Read(url=url)
        info = self.controls.label[1]


class EnvironmentZone(Zone, Runner):

    def __init__(self, parent, name="", **kwargs):
        super().__init__(parent, name=name, **kwargs)
        self.activity = list()

    def build(self, frame: ttk.Frame):
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=0)
        frame.rowconfigure(2, weight=10)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=10)
        frame.columnconfigure(2, weight=2)
        frame.columnconfigure(3, weight=2)

        yield "label", self.grid(ttk.Label(frame, text="Directory"), row=0, column=0, padx=(10, 10))
        yield "entry", self.grid(ttk.Entry(frame), row=0, column=1, pady=(10, 10), ipadx=1, ipady=2, sticky=tk.W + tk.E)

        yield "button", self.grid(
            tk.Button(frame, text="Select", command=self.on_select),
            row=0, column=2, padx=(10, 10), sticky=tk.W + tk.E
        )

        yield "button", self.grid(
            tk.Button(frame, text="Build", command=self.on_build),
            row=0, column=3, columnspan=2, padx=(10, 10), sticky=tk.W + tk.E
        )

        yield "progress", self.grid(
            ttk.Progressbar(frame, orient=tk.HORIZONTAL),
            row=1, column=0, columnspan=4, padx=(10, 10), pady=(10, 10), sticky=tk.W + tk.E
        )

        text_widget = tk.Text(frame, height=6)
        scroll_bar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scroll_bar.set)
        yield "text", self.grid(text_widget, row=2, column=0, columnspan=4, padx=(10, 10), sticky=tk.W + tk.N + tk.E + tk.S)
        yield "scroll", self.grid(scroll_bar, row=2, column=4, pady=(10, 10), sticky=tk.N + tk.S)

    def on_select(self):
        path = pathlib.Path(filedialog.askdirectory(
            parent=self.frame,
            title="Select virtual environment",
            initialdir=pathlib.Path.cwd(),
            mustexist=True,
        ))
        if not self.venv_cfg(path) and not path.name.startswith("busker_"):
            path = pathlib.Path(tempfile.mkdtemp(prefix="busker_", suffix="_venv", dir=path))
        self.controls.entry[0].delete(0, tk.END)
        self.controls.entry[0].insert(0, str(path))

    def on_build(self):
        path = pathlib.Path(self.controls.entry[0].get())
        future = self.executor.submit(
            venv.create,
            path,
            system_site_packages=True,
            clear=True,
            with_pip=True,
            upgrade_deps=True
        )
        future.add_done_callback(self.on_complete)
        self.update_progress(path, future)

    def on_complete(self, future):
        for bar in self.controls.progress:
            bar["value"] = 0
            self.activity.clear()

    def update_progress(self, path: pathlib.Path, future=None):
        files = list(self.walk_files(path))
        self.activity.append(len(files))

        if future and not future.done():
            for bar in self.controls.progress:
                # TODO: Better approximation of progress
                half = 50 if self.activity[-1] < max(self.activity) else 0
                bar["value"] = min(half + len(self.activity) * 8, 100)

            self.frame.after(1500, self.update_progress, path, future)


class PackageZone(Zone):

    def build(self, frame: ttk.Frame):
        frame.rowconfigure(0, weight=0)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=10)
        frame.columnconfigure(2, weight=2)
        frame.columnconfigure(3, weight=2)

        yield "label", self.grid(ttk.Label(frame, text="Source"), row=0, column=0, padx=(10, 10))
        yield "entry", self.grid(ttk.Entry(frame), row=0, column=1, pady=(10, 10), ipadx=1, ipady=2, sticky=tk.W + tk.E)

        yield "button", self.grid(
            tk.Button(frame, text="Select", command=self.on_select),
            row=0, column=2, padx=(10, 10), sticky=tk.W + tk.E
        )

        yield "button", self.grid(
            tk.Button(frame, text="Install", command=self.on_install),
            row=0, column=3, columnspan=2, padx=(10, 10), sticky=tk.W + tk.E
        )

    def on_select(self):
        path = pathlib.Path(filedialog.askdirectory(
            parent=self.frame,
            title="Select virtual environment",
            initialdir=pathlib.Path.cwd(),
            mustexist=True,
        ))
        if not self.venv_cfg(path) and not path.name.startswith("busker_"):
            path = pathlib.Path(tempfile.mkdtemp(prefix="busker_", suffix="_venv", dir=path))
        self.controls.entry[0].delete(0, tk.END)
        self.controls.entry[0].insert(0, str(path))

    def on_install(self):
        path = pathlib.Path(self.controls.entry[0].get())
        future = self.executor.submit(
            venv.create,
            path,
            system_site_packages=True,
            clear=True,
            with_pip=True,
            upgrade_deps=True
        )
        future.add_done_callback(self.on_complete)
        self.update_progress(path, future)

    def on_complete(self, future):
        for bar in self.controls.progress:
            bar["value"] = 0
            self.activity.clear()

    def update_progress(self, path: pathlib.Path, future=None):
        files = list(self.walk_files(path))
        self.activity.append(len(files))

        if future and not future.done():
            for bar in self.controls.progress:
                # TODO: Better approximation of progress
                half = 50 if self.activity[-1] < max(self.activity) else 0
                bar["value"] = min(half + len(self.activity) * 8, 100)

            self.frame.after(1500, self.update_progress, path, future)


class ServerZone(Zone):

    def build(self, frame: ttk.Frame):
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        yield "label", self.grid(ttk.Label(frame, text="Entry point"), row=0, column=0, padx=(10, 10))
        yield "entry", self.grid(ttk.Entry(frame, justify=tk.LEFT, width=24), row=0, column=1, padx=(10, 10))

        yield "label", self.grid(ttk.Label(frame, text="Host"), row=0, column=2, padx=(10, 10))
        combo_box = ttk.Combobox(frame, justify=tk.LEFT, width=14, values=[i.value for i in Host])
        combo_box.current(0)
        yield "entry", self.grid(combo_box, row=0, column=3, padx=(10, 10))

        yield "label", self.grid(ttk.Label(frame, text="Port"), row=0, column=4, padx=(10, 10))
        spin_box = ttk.Spinbox(frame, justify=tk.LEFT, width=4, values=(80, 8000, 8001, 8080, 8081, 8082, 8088))
        spin_box.set(8080)
        yield "entry", self.grid(spin_box, row=0, column=5, padx=(10, 10))

        yield "button", self.grid(
            tk.Button(frame, text="Activate", command=self.on_activate),
            row=0, column=6, padx=(10, 10), sticky=tk.E
        )
        text_widget = tk.Text(frame, height=6)
        text_widget.insert(tk.END, "asdfghjrtyuhjk\njnion" * 150)
        scroll_bar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scroll_bar.set)
        yield "text", self.grid(text_widget, row=1, column=0, columnspan=6, padx=(10, 10), sticky=tk.E + tk.W)
        yield "scroll", self.grid(scroll_bar, row=1, column=6, pady=(10, 10), sticky=tk.N + tk.S)

    def on_activate(self):
        print(self.controls)


def build(config: dict = {}):
    root = tk.Tk()
    root.title(f"Busker {busker.__version__}")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    notebook = ttk.Notebook(root)
    notebook.grid(row=0, column=0, sticky=tk.N + tk.E + tk.S + tk.W)


    pages = [
        Structure(
            name="Playing",
            frame=tk.Frame(notebook),
            zones = []
        ),
        Structure(
            name="Hosting",
            frame=tk.Frame(notebook),
            zones = []
        ),
        Structure(
            name="Plugins",
            frame=tk.Frame(notebook),
            zones = []
        ),
    ]

    pages[0].zones.extend([
        InfoZone(pages[0].frame, name="Info"),
        InteractiveZone(pages[0].frame, name="Interactive"),
    ])
    pages[1].zones.extend([
        EnvironmentZone(pages[1].frame, name="Environment"),
        PackageZone(pages[1].frame, name="Package"),
        ServerZone(pages[1].frame, name="Server"),
    ])


    for p, page in enumerate(pages):
        page.frame.grid()
        notebook.add(page.frame, text=page.name)
        if p == 0:
            page.frame.rowconfigure(0, weight=1)
            page.frame.rowconfigure(1, weight=15)
            page.frame.columnconfigure(0, weight=1)
            page.zones[0].frame.grid(row=0, column=0, padx=(2, 2), pady=(6, 1), sticky=tk.N + tk.E + tk.S + tk.W)
            page.zones[1].frame.grid(row=1, column=0, padx=(2, 2), pady=(6, 1), sticky=tk.N + tk.E + tk.S + tk.W)
        elif p == 1:
            page.frame.rowconfigure(0, weight=1)
            page.frame.rowconfigure(1, weight=0)
            page.frame.rowconfigure(2, weight=1)
            page.frame.columnconfigure(0, weight=1)
            page.zones[0].frame.grid(row=0, column=0, padx=(2, 2), pady=(6, 1), sticky=tk.N + tk.E + tk.S + tk.W)
            page.zones[1].frame.grid(row=1, column=0, padx=(2, 2), pady=(6, 1), sticky=tk.E + tk.W)
        else:
            page.frame.columnconfigure(0, weight=1)

            for z, zone in enumerate(page.zones):
                page.frame.rowconfigure(z, weight=1)
                zone.frame.grid(row=z, column=0, sticky=tk.N + tk.E + tk.S + tk.W)

    root.minsize(720, 480)
    return root


if __name__ == "__main__":
    root = build()
    root.mainloop()
