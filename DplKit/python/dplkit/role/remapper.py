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


class aRemapper(object):
    """
    """
    __metaclass__ = ABCMeta

    provides = None     # similar to .meta, a mapping of what channels are provided, use @property to provide an active form
    requires = None

    @property
    def meta(self):
        return self.provides
    # FUTURE: decide on standardization of meta vs provides+requires attributes

    def __init__(self, *args, **kwargs):
        """
        """
        super(aRemapper, self).__init__()
        self._url = url

    @abstractmethod
    def reproject(self, *args, **kwargs):
        """
        change the projection coordinates of a dataset to match the configured projection
        """
        pass

    def __iter__(self):
        return self.reproject()

    def __call__(self, *args, **kwargs):
        """
        """
        return self.reproject(*args, **kwargs)
        







#
## Code goes here.
#


def test():
    """ """
    pass


if __name__=='__main__':
    test()
