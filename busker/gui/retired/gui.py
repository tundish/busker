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
import importlib.metadata
import logging
import multiprocessing.context
import os
import pathlib
import queue
import subprocess
import tempfile
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from types import SimpleNamespace as Structure
import sys
import urllib.error
import urllib.parse
import venv

import busker
from busker.executive import Executive
from busker.history import SharedHistory
from busker.runner import Installation
from busker.runner import Discovery
from busker.runner import Runner
from busker.runner import Server
from busker.runner import VirtualEnv
from busker.scraper import Node
from busker.scraper import Scraper
from busker.tagger import Tagger
from busker.types import ExecutionEnvironment
from busker.types import Host
import busker.visitor
from busker.visitor import Choice
from busker.zone import Zone


class InfoZone(Zone):

    def __init__(self, parent, name="", **kwargs):
        super().__init__(parent, name=name, **kwargs)
        self.scraper = Scraper()

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
        reader = busker.visitor.Read(url=url)
        info = self.controls.label[1]
        try:
            node = reader.run(self.scraper)
        except (ValueError, urllib.error.URLError) as e:
            info.configure(text="No connection to host")
            self.log(f"{e!s}", level=logging.WARNING)
            return
        else:
            info.configure(text=node.text.strip())

        reader = busker.visitor.Read(url=host)
        node = reader.run(self.scraper)
        writer = busker.visitor.Write(url=host, prior=node, choice=Choice(form="ballad-form-start"))
        self.registry["Transcript"].process_node(writer.run(self.scraper))


class InteractiveZone(Zone):

    def __init__(self, parent, name="", **kwargs):
        self.assist = tk.BooleanVar(value=False)
        super().__init__(parent, name=name, **kwargs)
        self.scraper = Scraper()
        self.node = None
        self.do_display()

    def build(self, frame: ttk.Frame):
        frame.rowconfigure(0, weight=30)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        text_widget = Tagger.configure(tk.Text(frame, height=6))
        scroll_bar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scroll_bar.set)

        yield "text", self.grid(text_widget, row=0, column=0, columnspan=3, padx=(10, 10), sticky=tk.W + tk.N + tk.E + tk.S)
        yield "scroll", self.grid(scroll_bar, row=0, column=3, pady=(10, 10), sticky=tk.N + tk.S)

        combo_box = ttk.Combobox(frame, justify=tk.LEFT)
        yield "entry", self.grid(
            combo_box, row=1, column=0,
            padx=(10, 10), pady=(2, 6), ipadx=6,
            sticky=tk.W + tk.N + tk.E + tk.S
        )
        combo_box.bind("<Return>", self.on_entry)

        yield "toggle", self.grid(
            ttk.Checkbutton(frame, variable=self.assist, offvalue=False, onvalue=True, command=self.do_display),
            row=1, column=1, padx=(10, 10), sticky=tk.W + tk.E
        )
        yield "label", self.grid(ttk.Label(frame, text="Assist"), row=1, column=2, columnspan=3, padx=(10, 10))

    def process_node(self, node: Node):
        self.node = node
        tagger = Tagger(self.controls.text[0])
        for block in node.blocks:
            tagger.feed(block)

    def do_display(self):
        if self.assist.get():
            Tagger.show(self.controls.text[0], "cue")
            if self.node:
                self.controls.entry[0].configure(values=self.node.options)
        else:
            Tagger.hide(self.controls.text[0], "cue")
            self.controls.entry[0].configure(values=[])

    def on_entry(self, evt):
        value = self.controls.entry[0].get().strip()
        writer = busker.visitor.Write(
            url=self.node.url,
            prior=self.node,
            choice=Choice(form="ballad-command-form", input="ballad-command-form-input-text", value=value)
        )
        self.controls.entry[0].delete(0, tk.END)

        Tagger.display_command(self.controls.text[0], cmd=value)
        try:
            self.process_node(writer.run(self.scraper))
        except urllib.error.HTTPError:
            Tagger.display_message(self.controls.text[0])
        finally:
            self.do_display()


class EnvironmentZone(Zone):

    def __init__(self, parent, name="", **kwargs):
        super().__init__(parent, name=name, **kwargs)
        self.executive = Executive()
        self.running = defaultdict(list)
        self.location = None
        self.interpreter = None

    def build(self, frame: ttk.Frame):
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, minsize=12)
        frame.columnconfigure(1, weight=10)
        frame.columnconfigure(2, weight=2)
        frame.columnconfigure(3, weight=2)

        yield "label", self.grid(ttk.Label(frame, text="Directory", width=8), row=0, column=0, padx=(10, 10))
        yield "entry", self.grid(ttk.Entry(frame), row=0, column=1, pady=(10, 10), ipadx=1, ipady=2, sticky=tk.W + tk.E)

        yield "button", self.grid(
            tk.Button(frame, text="Select", command=self.on_select),
            row=0, column=2, padx=(10, 10), sticky=tk.W + tk.E
        )

        yield "button", self.grid(
            tk.Button(frame, text="Build", command=self.on_build),
            row=0, column=3, columnspan=2, padx=(10, 10), sticky=tk.W + tk.E
        )

    def on_select(self):
        choice = filedialog.askdirectory(
            parent=self.frame,
            title="Select virtual environment",
            initialdir=pathlib.Path.cwd(),
            mustexist=True,
        )
        if not choice:
            return
        else:
            path = pathlib.Path(choice)

        if not self.executive.venv_cfg(path) and not path.name.startswith("busker_"):
            path = pathlib.Path(tempfile.mkdtemp(prefix="busker_", suffix="_venv", dir=path))
        self.controls.entry[0].delete(0, tk.END)
        self.controls.entry[0].insert(0, str(path))
        self.location = path

    def on_build(self):
        path = pathlib.Path(self.controls.entry[0].get())
        runner = VirtualEnv(path)
        self.registry["Output"].controls.text[0].insert(
            tk.END,
            f"{self.executive.active.interpreter} is active.\n"
        )
        self.running[runner.uid] = list(self.executive.run(runner, callback=self.on_complete))
        self.registry["Output"].controls.text[0].insert(tk.END, f"Environment build begins.\n")
        self.update_progress(runner)

    def on_complete(self, result):
        pending = self.running[result.runner.uid]
        pending.pop(0)
        if pending: return

        self.interpreter = self.executive.register(self.location)
        self.registry["Output"].controls.text[0].insert(tk.END, f"Environment build complete.\n")

        self.executive.shutdown(self.executive.active)
        self.executive.activate(self.executive.registry[self.interpreter])
        self.registry["Output"].controls.text[0].insert(
            tk.END,
            f"{self.executive.active.interpreter} is active.\n"
        )
        self.registry["Package"].controls.button[1]["state"] = tk.NORMAL

    def update_progress(self, runner: Runner):
        running = self.running[runner.uid]
        for result in running:
            while not result.exenv.queue.empty():
                count = result.exenv.queue.get(block=False)
                self.registry["Output"].controls.text[0].insert(
                    tk.END, f"Environment objects counted: {count}\n"
                )

        if not all(r.ready() for r in running):
            self.frame.after(500, self.update_progress, runner)


class PackageZone(Zone):

    def __init__(self, parent, name="", **kwargs):
        super().__init__(parent, name=name, **kwargs)
        self.executive = Executive()
        self.running = defaultdict(list)

    def build(self, frame: ttk.Frame):
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, minsize=12)
        frame.columnconfigure(1, weight=10)
        frame.columnconfigure(2, weight=2)
        frame.columnconfigure(3, weight=2)

        yield "label", self.grid(ttk.Label(frame, text="Source", width=8), row=0, column=0, padx=(10, 10))
        yield "entry", self.grid(ttk.Entry(frame), row=0, column=1, pady=(10, 10), ipadx=1, ipady=2, sticky=tk.W + tk.E)

        yield "button", self.grid(
            tk.Button(frame, text="Select", command=self.on_select),
            row=0, column=2, padx=(10, 10), sticky=tk.W + tk.E
        )

        install_button = self.grid(
            tk.Button(frame, text="Install", command=self.on_install),
            row=0, column=3, columnspan=2, padx=(10, 10), sticky=tk.W + tk.E
        )
        install_button["state"] = tk.DISABLED
        yield "button", install_button

    def on_select(self):
        path = pathlib.Path(filedialog.askopenfilename(
            parent=self.frame,
            title="Select Python package",
            initialdir=pathlib.Path.cwd(),
            filetypes=[
                ("Source packages", "*.tar.gz"),
                ("Binary packages", "*.whl"),
            ]
        ))
        self.controls.entry[0].delete(0, tk.END)
        self.controls.entry[0].insert(0, str(path))

    def on_install(self):
        interpreter = self.registry["Environment"].interpreter
        if not interpreter or interpreter not in self.executive.registry:
            tk.messagebox.showwarning(message="No interpreter.\nPlease select and build an environment.")
            return

        path = pathlib.Path(self.controls.entry[0].get())
        runner = Installation(path)

        self.running[runner.uid] = list(self.executive.run(runner, interpreter=interpreter, queue=queue.Queue()))
        self.registry["Output"].controls.text[0].insert(tk.END, f"Package installation begins.\n")
        self.update_progress(runner)

    def update_progress(self, runner: Runner):
        line = runner.proc.stdout.readline()

        text_widget = self.registry["Output"].controls.text[0]
        text_widget.insert(tk.END, line)
        text_widget.see(tk.END)

        try:
            msg = runner.exenv.queue.get(block=False)
            if isinstance(msg, list):
                msg = [str(i) for i in msg]
            text_widget.insert(tk.END, f"Runner: {msg}\n")
            text_widget.see(tk.END)
        except queue.Empty:
            pass

        if runner.proc.poll() is None:
            self.frame.after(100, self.update_progress, runner)
        else:
            self.install_complete(runner)

    def install_complete(self, runner: Runner):
        text_widget = self.registry["Output"].controls.text[0]
        for line in runner.proc.stdout.read().splitlines(keepends=True):
            text_widget.insert(tk.END, line)
        for line in runner.proc.stderr.read().splitlines(keepends=True):
            text_widget.insert(tk.END, line)
        text_widget.see(tk.END)

        package_path = runner.distribution
        runner = Discovery()
        proc = next(self.executive.run(runner, interpreter=self.executive.active.interpreter))
        out, err = proc.communicate()

        entry_points = runner.filter_entry_points([i.strip() for i in out.splitlines()])
        name = package_path.name.removesuffix("".join(package_path.suffixes))
        values = runner.sort_entry_points(entry_points, like=name)

        entry_widget = self.registry["Server"].controls.entry[0]
        entry_widget.configure(values=values)
        entry_widget.current(0)
        self.registry["Server"].controls.button[1]["state"] = tk.NORMAL
        proc.terminate()


class ServerZone(Zone):

    def __init__(self, parent, name="", **kwargs):
        super().__init__(parent, name=name, **kwargs)
        self.executive = Executive()
        self.running = None
        parent._root().protocol('WM_DELETE_WINDOW', self.on_window)

    def build(self, frame: ttk.Frame):
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, minsize=12)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(6, uniform="button")
        frame.columnconfigure(7, uniform="button")

        yield "label", self.grid(ttk.Label(frame, text="Entry point"), row=0, column=0, padx=(10, 10))
        yield "entry", self.grid(
            ttk.Combobox(frame, justify=tk.LEFT),
            row=0, column=1, padx=(10, 10), sticky=tk.W + tk.E
        )

        yield "label", self.grid(ttk.Label(frame, text="Host"), row=0, column=2, padx=(10, 10))
        combo_box = ttk.Combobox(frame, justify=tk.LEFT, width=14, values=[i.value for i in Host])
        combo_box.current(0)
        yield "entry", self.grid(combo_box, row=0, column=3, padx=(10, 10))

        yield "label", self.grid(ttk.Label(frame, text="Port"), row=0, column=4, padx=(10, 10))
        spin_box = ttk.Spinbox(frame, justify=tk.LEFT, width=4, values=(80, 8000, 8001, 8080, 8081, 8082, 8088))
        spin_box.set(8080)
        yield "entry", self.grid(spin_box, row=0, column=5, padx=(10, 10))

        buttons = [
            self.grid(
                tk.Button(frame, text="Stop", command=self.on_stop),
                row=0, column=6, padx=(10, 10), pady=(10, 10), sticky=tk.W + tk.E
            ),
            self.grid(
                tk.Button(frame, text="Start", command=self.on_start),
                row=0, column=7, padx=(10, 10), pady=(10, 10), sticky=tk.W + tk.E
            ),
        ]
        for button in buttons:
            # button["state"] = tk.DISABLED
            yield "button", button

    def on_window(self):
        if not self.running:
            self.parent._root().destroy()
        elif messagebox.askokcancel("Quit", "Quitting now will stop the server."):
            self.on_stop()
            self.parent._root().destroy()

    def on_stop(self):
        text_widget = self.registry["Output"].controls.text[0]
        self.controls.button[0]["state"] = tk.DISABLED
        self.controls.button[1]["state"] = tk.NORMAL

        if self.running:
            self.running.terminate()
            text_widget.insert(tk.END, f"Server process terminated.\n")
            text_widget.see(tk.END)
            self.running = None

    def on_start(self):
        text_widget = self.registry["Output"].controls.text[0]
        self.controls.button[0]["state"] = tk.NORMAL
        self.controls.button[1]["state"] = tk.DISABLED

        entry_point = self.controls.entry[0].get()
        host = self.controls.entry[1].get().strip()
        port = self.controls.entry[2].get()
        text_widget.insert(tk.END, f"Starting {entry_point} on {host}:{port}.\n")
        text_widget.see(tk.END)

        runner = Server(entry_point, host=host, port=port)
        self.running = next(self.executive.run(runner, interpreter=self.executive.active.interpreter))

        self.registry["Info"].controls.entry[0].delete(0, tk.END)
        self.registry["Info"].controls.entry[0].insert(0, runner.url)
        text_widget.insert(tk.END, f"Server process running.\n")
        text_widget.see(tk.END)

        os.set_blocking(self.running.stdout.fileno(), False)
        os.set_blocking(self.running.stderr.fileno(), False)
        self.update_progress(runner)

    def update_progress(self, runner: Runner):
        text_widget = self.registry["Output"].controls.text[0]

        try:
            msg = runner.exenv.queue.get(block=False)
            if isinstance(msg, list):
                msg = [str(i) for i in msg]
            text_widget.insert(tk.END, f"Runner: {msg}\n")
            text_widget.see(tk.END)
        except queue.Empty:
            pass

        for line in runner.proc.stdout:
            text_widget.insert(tk.END, line)
            text_widget.see(tk.END)
        for line in runner.proc.stderr:
            text_widget.insert(tk.END, line)
            text_widget.see(tk.END)

        if runner.proc.poll() is None:
            self.frame.after(100, self.update_progress, runner)


class OutputZone(Zone):

    def build(self, frame: ttk.Frame):
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=30)
        frame.columnconfigure(1, weight=1)

        text_widget = tk.Text(frame)
        scroll_bar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scroll_bar.set)
        yield "text", self.grid(text_widget, row=0, column=0, padx=(10, 10), sticky=tk.W + tk.N + tk.E + tk.S)
        yield "scroll", self.grid(scroll_bar, row=0, column=1, pady=(10, 10), sticky=tk.N + tk.S)


def build(config: dict = {}, exclude=set()):
    root = tk.Tk()
    root.title(f"Busker {busker.__version__}")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    notebook = ttk.Notebook(root)
    notebook.grid(row=0, column=0, sticky=tk.N + tk.E + tk.S + tk.W)


    pages = [
        Structure(
            name="Interactive",
            frame=tk.Frame(notebook),
            zones = []
        ),
        Structure(
            name="Hosting",
            frame=tk.Frame(notebook),
            zones = []
        ),
        Structure(
            name="Automation",
            frame=tk.Frame(notebook),
            zones = []
        ),
    ]

    pages[0].zones.extend([
        InfoZone(pages[0].frame, name="Info"),
        InteractiveZone(pages[0].frame, name="Transcript"),
    ])
    pages[1].zones.extend([
        EnvironmentZone(pages[1].frame, name="Environment"),
        PackageZone(pages[1].frame, name="Package"),
        ServerZone(pages[1].frame, name="Server"),
        OutputZone(pages[1].frame, name="Output"),
    ])


    for p, page in enumerate(pages):
        page.frame.grid()
        if page.name.lower() not in exclude:
            notebook.add(page.frame, text=page.name)
        if p == 0:
            page.frame.rowconfigure(0, weight=1)
            page.frame.rowconfigure(1, weight=25)
            page.frame.columnconfigure(0, weight=1)
            page.zones[0].frame.grid(row=0, column=0, padx=(2, 2), pady=(6, 2), sticky=tk.N + tk.E + tk.S + tk.W)
            page.zones[1].frame.grid(row=1, column=0, padx=(2, 2), pady=(6, 2), sticky=tk.N + tk.E + tk.S + tk.W)
        elif p == 1:
            page.frame.rowconfigure(0, weight=0)
            page.frame.rowconfigure(1, weight=0)
            page.frame.rowconfigure(3, weight=10)
            page.frame.columnconfigure(0, weight=1)
            for z, zone in enumerate(page.zones):
                zone.frame.grid(row=z, column=0, padx=(2, 2), pady=(6, 2), sticky=tk.N + tk.E + tk.S + tk.W)
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
