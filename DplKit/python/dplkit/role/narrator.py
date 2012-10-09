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

LOG = logging.getLogger(__name__)


class aNarrator(object):
    """Narrator(uri, **constraints) generates a framestream from a media URI.
    It also provides a meta mapping as an attribute.
    """
    provides = None     # similar to .meta, a mapping of what channels are provided, use @property to provide an active form

    @property
    def meta(self):
        return self.provides

    def __init__(self, media_uri_seq, *args, **kwargs):
        """given media information and constraint arguments, initialize the narrator
        """
        super(aNarrator, self).__init__()
        self._media_uri_seq = media_uri_seq

    def __call__(self, **kwargs):
        """yield a series of frames from the desired part of the input file or files
        """
        pass
        


def test(*args):
    """ """
    pass
    


if __name__=='__main__':
    from sys import argv
    test(*argv[1:])
