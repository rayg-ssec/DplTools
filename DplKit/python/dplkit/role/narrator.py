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
from abc import ABCMeta, abstractmethod

LOG = logging.getLogger(__name__)


class aNarrator(object):
    """Narrator(url, **constraints) generates a framestream from a media URI.
    It also provides a meta mapping as an attribute.
    """
    __metaclass__ = ABCMeta

    provides = None     # similar to .meta, a mapping of what channels are provided, use @property to provide an active form

    @property
    def meta(self):
        return self.provides
    # FUTURE: decide on standardization of meta vs provides+requires attributes

    def __init__(self, url, *args, **kwargs):
        """given media information and constraint arguments, initialize the narrator
        """
        super(aNarrator, self).__init__()
        self._url = url

    @abstractmethod
    def read(self, *args, **kwargs):
        """
        Yield a series of frames from the desired part of the input file or files
        """
        pass

    def __iter__(self):
        return self.read()

    def __call__(self, *args, **kwargs):
        """
        Read the media and yield a series of data frames (see .read())
        """
        return self.read(*args, **kwargs)
        


def test(*args):
    """ """
    pass
    


if __name__=='__main__':
    from sys import argv
    test(*argv[1:])
