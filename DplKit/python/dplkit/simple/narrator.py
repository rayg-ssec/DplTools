#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.role.narrator
~~~~~~~~~~~~~~~~~~~~

A Narrator is initialized with a sequence of equivalent media URIs,
and when called, generates a series of data frames.

The narrator is created one-per-media-uri,
optionally one-per-media-uri-sequence iff it makes the
most sense to implicitly catenate media file contents.




:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""

import os, sys
import logging

from ..role.narrator import aNarrator
from ..frame.struct import struct
from numpy import array

LOG = logging.getLogger(__name__)




class CsvNarrator(aNarrator):
    """Example CSV file narrator yielding dictionaries as frames.
    dplkit.frame.carrier objects could also be used.
    """
    _csv = None

    def __init__(self, url, **kwargs):
        from csv import DictReader
        from urllib2 import urlopen
        self._csv = csv = DictReader(urlopen(url))
        self.provides = dict((name, None) for name in csv.fieldnames)

    def read(self, *args, **kwargs):
        for row in self._csv:
            yield struct(row, meta=self.meta)



def test(*args):
    """ """
    from pprint import pprint
    tcn = CsvNarrator(*args)
    for frame in tcn:
        pprint(frame)
    pprint(list(tcn.meta.keys()))



if __name__=='__main__':
    from sys import argv
    test(*argv[1:])
