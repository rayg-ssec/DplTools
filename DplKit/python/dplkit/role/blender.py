#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
package.module
~~~~~~~~~~~~~~


A description which can be long and explain the complete
functionality of this module even with indented code examples.
Class/Function however should not be documented here.


:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""

import os, sys
import logging
from abc import ABCMeta, abstractmethod
from dplkit.role.filter import aFilter

LOG = logging.getLogger(__name__)


class aBlender(aFilter):
    """
    A blender combines one or more frame streams into a single outgoing stream. Its primary activity is combine()
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def combine(self, *args, **kwargs):
        """
        """        
        pass

    def process(self, *args, **kwargs):
        return self.combine(*args, **kwargs)



class Merge(aBlender):
    def __init__(self, *sources, **kwargs):
        super(self.__class__, self).__init__()
        self._sources = sources

    def combine(self, *args, **kwargs):
        from ..frame.struct import struct
        for framegroup in zip(self._sources):
            f = struct(framegroup[0])
            for q in framegroup[1:]:
                vars(f).update(vars(q))
            yield f.as_dict()



#
## Code goes here.
#


def test():
    """ """
    pass


if __name__=='__main__':
    test()
