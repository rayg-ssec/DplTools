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
from dplkit.role.filter import aFilter

LOG = logging.getLogger(__name__)


class aArtist(aFilter):
    """
    Artists convert frame streams into viewable images. Their primary action is render().
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def render(self, *args, **kwargs):
        """
        """        
        pass

    def process(self, *args, **kwargs):
        return self.render(*args, **kwargs)





#
## Code goes here.
#


def test():
    """ """
    pass


if __name__=='__main__':
    test()
