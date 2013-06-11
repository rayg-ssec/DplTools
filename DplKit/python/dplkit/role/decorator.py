#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.role.decorator
~~~~~~~~~~~~~~~~~~~~~

Decorators used to mix-in standard protocols

:copyright: 2013 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""
__author__ = 'rayg'
__docformat__ = 'reStructuredText'

import os, sys
import logging, unittest
from functools import wraps

LOG = logging.getLogger(__name__)


def has_provides(cls):
    class new_cls(cls):
        __doc__ = getattr(cls, '__doc__', "")
        provides = None
        @property
        def meta(self):
            return self.provides
    return new_cls


def has_requires(cls):
    class new_cls(cls):
        __doc__ = getattr(cls, '__doc__', "")
        requires = None
    return new_cls

