#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.role.artist
~~~~~~~~~~~~~~~~~~

Artist takes in a frame stream, and writes out images or other visual representations.

:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""

import os, sys
import logging
from abc import ABCMeta, abstractmethod

LOG = logging.getLogger(__name__)


class aArtist(object):
    """
    Artists convert frame streams into viewable images. Their primary action is render().
    """
    __metaclass__ = ABCMeta
    requires = None  # mapping of information about what it needs from upstream

    def __init__(self, source, **kwargs):
        """
        """
        super(aArtist, self).__init__()
        pass

    @abstractmethod
    def render(self, *args, **kwargs):
        """
        """        
        pass

    def __iter__(self):
        return self.render()

    def __call__(self, *args, **kwargs):
        "the default action of an artist is to render"
        return self.render(*args, **kwargs)




#
## Code goes here.
#


def test():
    """ """
    pass


if __name__=='__main__':
    test()
