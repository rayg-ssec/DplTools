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

LOG = logging.getLogger(__name__)


class aFilter(object):
    """
    Filters modify one or more input frame-streams to produce one or more output data-streams.
    """
    provides = None  # mapping of information about channels this filter provides, similar to .meta on frames
    requires = None  # mapping of information about what it needs from upstream

    @property
    def meta(self):
        return self.provides

    def __init__(self, upstream_seq, **kwargs):
        """

        """
        pass

    def __call__(self):
        pass




def test():
    """ """
    pass


if __name__=='__main__':
    test()
