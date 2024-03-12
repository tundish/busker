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

from collections import deque
import datetime
import logging
import tomllib
import unittest

from busker.history import SharedHistory


class TOMLTests(unittest.TestCase):

    def test_log_records(self):
        data = dict(
            args=("a", "b", "c"),
            funcName="test_log_records",
            levelname="INFO",
            levelno=20,
            msg="Learn your %s%s%s 's",
            name="TOMLTestLogger",
            pathname="busker/test/test_history.py",
            processName="MainProcess",
        )
        records = dict(
            records=deque([
                logging.makeLogRecord(dict(data, asctime=datetime.datetime.now().isoformat(), lineno=n * 10))
                for n in range(12)
            ])
        )
        lines = list(SharedHistory().toml_lines(records))
        text = "\n".join(lines)
        data = tomllib.loads("\n".join(lines))
        self.assertTrue(data)
        output = data.get("log", {}).get("records", [])
        self.assertTrue(output, data)
        record = logging.makeLogRecord(output[0])
        print(vars(record))
        self.assertEqual(record.getMessage(), "s", vars(record))
