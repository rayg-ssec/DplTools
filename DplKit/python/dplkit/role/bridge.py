#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.role.bridge
~~~~~~~~~~~~~~~~~~

A bridge moves data from one transport mechanism to another, 
since framestreams can be moved in different representations.
Typically you'll want a bridge when you go between languages, 
or between machines or processes.


:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""

import os, sys
import logging
from abc import ABCMeta, abstractmethod

LOG = logging.getLogger(__name__)


class aBridge(object):
    """
    abstract bridge base. 
    Outgoing bridges act like artists; incoming bridges act like narrators.

    """
    __metaclass__ = ABCMeta
    provides = None
    requires = None
    @property
    def meta(self):
        return self.provides

    @abstractmethod
    def read(self, *args, **kwargs):
        pass

    @abstractmethod
    def process(self, *args, **kwargs):
        pass



class aIncomingBridge(aBridge):
    """
    abstract bridge base. 
    Outgoing bridges act like artists; incoming bridges act like narrators.

    """
    __metaclass__ = ABCMeta

    def __init__(self, source, *args, **kwargs):
        """given media information and constraint arguments, initialize the narrator
        """
        super(self.__class__, self).__init__()

    @abstractmethod
    def read(self, *args, **kwargs):
        pass

    def process(self, *args, **kwargs):
        raise NotImplementedError('unsupported process operation for incoming-only bridge')

    def __iter__(self):
        return self.read()

    def __call__(self, *args, **kwargs):
        """
        The default action of a narrator is to read from the provided media.
        """
        return self.read(*args, **kwargs)



class aOutgoingBridge(aBridge):
    """
    abstract bridge base.
    Implement process() and iterate ._source for input data
    """
    __metaclass__ = ABCMeta
    def __init__(self, source, *args, **kwargs):
        """given media information and constraint arguments, initialize the narrator
        """
        super(self.__class__, self).__init__()
        self._source = source
        self.provides = source.provides

    def read(self, *args, **kwargs):
        raise NotImplementedError('unsupported read operation for outgoing-only bridge')

    @abstractmethod
    def connect(self, *args, **kwargs):
        raise NotImplementedError('unsupported connect operation for outgoing-only bridge')

    @abstractmethod
    def send(self, frame):
        raise NotImplementedError('unsupported send operation for outgoing-only bridge')

    def process(self, *args, **kwargs):
        self.connect()
        for frame in self._source:
            self.send(frame)
        self.close()

    @abstractmethod
    def close(self):
        raise NotImplementedError('unsupported close operation for outgoing-only bridge')

    def __iter__(self):
        return self.process()

    def __call__(self, *args, **kwargs):
        return self.process(*args, **kwargs)





def test():
    """ """
    pass


if __name__=='__main__':
    test()
