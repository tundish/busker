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
import sys
import tomllib


class SharedLogRecord(logging.LogRecord):

    @classmethod
    def factory(
        cls, name: str, level: str, fn: str, lno: int,
        msg: str, args: tuple | dict,
        exc_info, func=None, sinfo=None,
        **kwargs
    ):
        return cls(
            name=name, level=level, pathname=fn, lineno=lno,
            msg=msg, args=args,
            exc_info=exc_info, func=func, sinfo=sinfo,
            **kwargs
        )

    def getMessage(self):
        try:
            return str(self.msg).format(**self.args)
        except TypeError:
            return str(self.msg).format(*self.args)


class SharedHistory:

    history = defaultdict(deque)

    class LogMemo(logging.Handler):

        def __init__(self, head, tail, level=logging.NOTSET):
            super().__init__(level=level)
            self.head = head
            self.tail = tail

        def emit(self, record):
            if len(self.head) < self.tail.maxlen:
                self.head.append(record)
            self.tail.append(record)

    def __init__(self, *args, maxlen: int = 24, **kwargs):
        self.log_name = kwargs.pop("log_name", "") or self.__class__.__name__.lower()

        super().__init__(*args, **kwargs)
        if "head" not in self.history:
            self.history["head"] = list()
        if "tail" not in self.history:
            self.history["tail"] = deque(maxlen=maxlen)

        logging.setLogRecordFactory(SharedLogRecord.factory)
        logger = logging.getLogger(self.log_name)
        logger.addHandler(self.LogMemo(self.history["head"], self.history["tail"]))

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
        for buffer in ("head", "tail"):
            yield f"{buffer} = ["
            for entry in data.get(buffer, []):
                record = vars(entry)
                items = ", ".join(f'"{k}" = {self.toml_type(record.get(k))}' for k in record_fields)
                yield f"{{ {items} }},"
            yield "]"

    def log(self, msg="", level=logging.INFO, *args, **kwargs):
        logger = logging.getLogger(self.log_name)
        return logger.log(level, msg, *args, **kwargs)
