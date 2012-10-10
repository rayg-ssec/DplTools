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
from abc import ABCMeta, abstractmethod

LOG = logging.getLogger(__name__)


class aFilter(object):
    """
    Filters modify one or more input frame-streams to produce one or more output data-streams.
    """
    __metaclass__ = ABCMeta
    provides = None  # mapping of information about channels this filter provides, similar to .meta on frames
    requires = None  # mapping of information about what it needs from upstream

    @property
    def meta(self):
        return self.provides

    def __init__(self, source, **kwargs):
        """
        A filter is initialized with a primary frame sequence (typically a generator provided by an upstream object)
        and any needed metadata to define its behavior. 

        Typically a filter is not re-used for multiple frame sequences.
        """
        super(aFilter, self).__init__()
        pass

    @abstractmethod
    def process(self, *args, **kwargs):
        """the default action of the filter is to process one framestream into another"""
        pass

    def __iter__(self):
        return self.process()

    def __call__(self, *args, **kwargs):
        "the default action of a filter is to process"
        return self.process(*args, **kwargs)




def test():
    """ """
    pass


if __name__=='__main__':
    test()
