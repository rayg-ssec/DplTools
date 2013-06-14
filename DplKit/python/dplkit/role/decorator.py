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


def exposes_attrs_of_field(fieldname):
    """
    decorator to allow class instances to return attributes of one of its fields, where the name is not already assigned
    :param fieldname: name of the attribute field which we should source attributes from if not already defined
    :param fieldname:
    :return:
    """
    def decorator(cl):
        oldcget = getattr(cl, '__getattr__', None)

        def _getattr_(self, name):
            if oldcget is not None:
                try:
                    return oldcget(self, name)
                except AttributeError:
                    pass
            source = self.__getattribute__(fieldname)
            return getattr(source, name)

        cl.__getattr__ = _getattr_
        return cl
    return decorator



class test_expose_attrs1(unittest.TestCase):

    class any(object):
        pass

    @exposes_attrs_of_field('src')
    class uncanny(object):
        src = None

        def __init__(self, _src):
            self.src = _src

    def test1(self):
        a = self.any()
        a.q = 'q'
        b = self.uncanny(a)
        self.assertEqual(b.q, a.q, 'check attribute passthrough')

    def test2(self):
        a = self.any()
        a.q = 'q'
        b = self.uncanny(a)
        b.q = 'r'
        self.assertNotEqual(b.q, a.q)

    def test3(self):
        a = self.any()
        a.q = 'q'
        b = self.uncanny(a)
        del a.q
        try:
            q = b.q
        except AttributeError:
            return True
        raise AttributeError('should not have resolved "q"')


if __name__=="__main__":
    import unittest
    unittest.main()
