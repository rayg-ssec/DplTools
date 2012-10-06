#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
package.module
~~~~~~~~~~~~~


A description which can be long and explain the complete
functionality of this module even with indented code examples.
Class/Function however should not be documented here.


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

    def __init__(self, uri, *args, **kwargs):
        """given a uri and constraint arguments, initialize the narrator
        """
        super(aNarrator, self).__init__()
        self.uri = uri

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

    def __init__(self, uri, **kwargs):
        from csv import DictReader
        from urllib2 import urlopen
        fp = urlopen(uri)
        self._csv = csv = DictReader(fp)
        self.meta = dict((name, None) for name in csv.fieldnames)


    def __call__(self, **kwargs):
        for row in self._csv:
            yield row






#
## Code goes here.
#


def test():
    """ """
    pass


if __name__=='__main__':
    test()
