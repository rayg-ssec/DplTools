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


def meta(self):
    return self.provides

def has_provides(cls):
    cls.provides = None
    cls.meta = property(meta)
    return cls


def has_requires(cls):
    cls.requires = None
    return cls

