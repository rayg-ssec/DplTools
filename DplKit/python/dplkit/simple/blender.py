#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.simple.blender
~~~~~~~~~~~~~~~~~~~~~



:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""

import os, sys
import logging
from ..role.blender import aBlender

LOG = logging.getLogger(__name__)



class Merge(aBlender):
    def __init__(self, *sources, **kwargs):
        super(Merge, self).__init__()
        self._sources = sources

    def combine(self, *args, **kwargs):
        from ..frame.struct import struct
        for framegroup in zip(self._sources):
            f = struct(framegroup[0])
            for q in framegroup[1:]:
                vars(f).update(vars(q))
            yield f






def test():
    """ """
    # FIXME 
    pass


if __name__=='__main__':
    test()
