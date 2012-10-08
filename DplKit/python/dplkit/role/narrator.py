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
# FUTURE: consider using ABCMeta, @abstractmethod from module abc
from numpy import array

LOG = logging.getLogger(__name__)


class aNarrator(object):
    """Narrator(uri, **constraints) generates a framestream from a media URI.
    It also provides a meta mapping as an attribute.
    """
    meta = None     # a mapping of what channels are provided, use @property to provide an active form

    def __init__(self, media_uri, *args, **kwargs):
        """given media information and constraint arguments, initialize the narrator
        """
        super(aNarrator, self).__init__()
        self._media_uri = media_uri

    def __call__(self, **kwargs):
        """yield a series of frames from the desired part of the input file or files
        """
        pass
        


class CsvNarrator(aNarrator):
    """Example CSV file narrator yielding dictionaries as frames.
    dplkit.frame.carrier objects could also be used.
    """
    _csv = None
    meta = None

    def __init__(self, urls, **kwargs):
        from csv import DictReader
        from urllib2 import urlopen
        self._csv = csv = [DictReader(urlopen(url)) for url in urls]
        self.meta = dict((name, None) for name in csv[0].fieldnames)

    def __call__(self, **kwargs):
        for csv in self._csv:
            for row in csv:
                yield row






#
## Code goes here.
#


def test(*args):
    """ """
    from pprint import pprint
    tcn = CsvNarrator(args)
    for frame in tcn():
        pprint(frame)
    pprint(list(tcn.meta.keys()))
    


if __name__=='__main__':
    from sys import argv
    test(*argv[1:])
