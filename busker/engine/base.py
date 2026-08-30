#!/usr/bin/env python
#   encoding: utf-8

# Copyright (C) 2026 D E Haynes
# This file is part of busker.

# Busker is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# Busker is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with busker.
# If not, see <https://www.gnu.org/licenses/>.


import sched
from busker.model.journal import Journal


class Engine:

    def __init__(self, rht: Journal = None):
        self.rht = rht
        self.scheduler = sched.scheduler()

    def put(self, *args, delay=0, **kwargs):
        callback = lambda x: x
        return [
            self.scheduler.enter(
                delay, n, callback, argument=(arg,), kwargs=kwargs
            )
            for n, arg in enumerate(args)
        ]

    def step(self, **kwargs):
        # run
        """
        delta = 0
        then = time.time()
        while delta is not None:
            await asyncio.sleep(delta)
            delta = scheduler.run(blocking=False)
        """
        return self.rht.marking
        pass
