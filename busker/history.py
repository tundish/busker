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
import logging
import pprint
import tomllib


class SharedHistory:

    history = defaultdict(deque)

    class LogMemo(logging.Handler):

        def __init__(self, buffer, level=logging.NOTSET):
            super().__init__(level=level)
            self.buffer = buffer

        def emit(self, record):
            self.buffer.append(record)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_name = self.__class__.__name__.lower()
        logger = logging.getLogger(self.log_name)
        logger.addHandler(self.LogMemo(self.history["records"]))

    @staticmethod
    def toml_type(obj):
        if isinstance(obj, (set, tuple)):
            return list(obj)
        elif isinstance(obj, str):
            return f'"{obj}"'
        return obj

    def toml_lines(self, data: dict):
        record_fields = (
            "args", "asctime", "funcName", "levelname", "levelno", "lineno",
            "msg", "name", "pathname", "processName",
        )
        yield "[log]"
        yield "records = ["
        for record in data.get("records", []):
            data = vars(record)
            items = ", ".join(f'"{k}" = {self.toml_type(data.get(k))}' for k in record_fields)
            yield f"{{ {items} }},"
        yield "]"

    def log(self, msg="", level=logging.INFO, *args, **kwargs):
        logger = logging.getLogger(self.log_name)
        return logger.log(level, msg, *args, **kwargs)