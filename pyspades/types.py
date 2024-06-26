# Copyright (c) Mathias Kaerlev 2011-2012.

# This file is part of pyspades.

# pyspades is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# pyspades is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with pyspades.  If not, see <http://www.gnu.org/licenses/>.

"""
A few useful types used around the place.

IDPool is used to distribute the IDs given out by the Server

AttributeSet is used for testing if various settings are active

MultikeyDict is used to make player names accessible by both id and name
"""

import itertools
from collections import deque


class OutOfIDsException(Exception):
    pass

class IDPool:
    """
    Manage pool of IDs

    >>> p = IDPool(start=10)
    >>> p.pop()
    10
    >>> p.pop()
    11
    >>> p.pop()
    12
    >>> p.put_back(11)
    >>> p.pop()
    11
    """

    def __init__(self, start=0, end=32):
        self.used_ids = []
        self.start = start
        self.end = end

    def pop(self):
        for id_ in range(self.start, self.end):
            if id_ not in self.used_ids:
                self.used_ids += [id_]
                return id_

        raise OutOfIDsException()

    def put_back(self, id_):
        self.used_ids.remove(id_)

class AttributeSet(set):
    """
    set with attribute access, i.e.

    >>> foo = AttributeSet(("eggs", ))
    >>> foo.eggs
    True
    >>> foo.spam
    False

    Also supports adding and removing elements

    >>> foo.bar = True
    >>> 'bar' in foo
    True
    >>> foo.bar = False
    >>> 'bar' in foo
    False

    This works as a quick shorthand for membership testing.
    """

    def __getattr__(self, name):
        return name in self

    def __setattr__(self, name, value):
        if value:
            self.add(name)
        else:
            self.discard(name)


class RateLimiter:
    """sliding window rate limiter

    Triggers if more than a certain number of events happen in a certain amount
    of time"""
    def __init__(self, event_count: int, seconds: float) -> None:
        """limit is event_count events in seconds"""
        self._seconds = seconds
        self._window = deque(maxlen=event_count)  # type: deque

    def record_event(self, timestamp: float) -> None:
        """record an event at the given timestamp"""
        self._window.append(timestamp)

    def above_limit(self) -> bool:
        if len(self._window) != self._window.maxlen:
            # not enough events yet
            return False

        start, end = self._window[0], self._window[-1]

        if end - start < self._seconds:
            return True
        return False

    def get_events(self) -> list:
        return list(self._window)
