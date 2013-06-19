#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.role.filter
~~~~~~~~~~~~~~~~~~


:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""

import os, sys
import logging
from abc import ABCMeta, abstractmethod
from dplkit.role.decorator import exposes_attrs_of_field, has_requires, has_provides

LOG = logging.getLogger(__name__)

@exposes_attrs_of_field('source')
@has_requires
@has_provides
class aFilter(object):
    """
    Filters modify one or more input frame-streams to produce one or more output data-streams.
    """
    __metaclass__ = ABCMeta
    source = None

    def __init__(self, source, **kwargs):
        """
        A filter is initialized with a primary frame sequence (typically a generator provided by an upstream object)
        and any needed metadata to define its behavior. 

        Typically a filter is not re-used for multiple frame sequences.
        """
        self.source = source

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
