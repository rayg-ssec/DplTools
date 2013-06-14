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

import threading

class realprovides:
    def __init__(self,n=[],g={},nesting=False,orig_iter=None):
        self.orig_iter=orig_iter
        self.nestedclasses=n if isinstance(n,list) else [n]
        self.getattributes=(g if isinstance(n,list) and isinstance(g,dict) else {type(n):g}) if g!=None else {}
        self.nesting=nesting

    def describe(self,frame):
        d=frame
        ret={}
        if not isinstance(frame,dict):
            d=None
            for c in self.nestedclasses:
                if isinstance(frame,c):
                    if c in self.getattributes:
                        d=self.getattributes[c](frame)
                    else:
                        d=vars(frame)
                    break
        if d==None:
            raise 'Unknown frame scope (possibly nested)'
        for k,v in d.items():
            if k.startswith('_'):
                continue
            ret[k]={'shortname':k,'type':type(v)}
            if self.nesting:
                for c in self.nestedclasses:
                    if isinstance(v,c):
                       ret[k]=self.describe(v)
                       break
        return ret

    def __call__(realme,self):
        if not self._dp_ranprovides:
            self._dp_provideslock.acquire()
            if not self._dp_ranprovides:
                try:
                    iterator=realme.orig_iter(self)#self.__iter__()
                    frames=[]
                    priorframe=None
                    while priorframe==None:
                        priorframe=iterator.next()
                        frames.append(priorframe)
                    self._dp_provides=realme.describe(priorframe)
                    self._dp_priorframes=frames
                    self._dp_iterator=iterator
                except StopIteration:
                    pass
                self._dp_ranprovides=True
            self._dp_provideslock.release()
        return self._dp_provides

def autoprovidenested(func=None,nestedclasses=[dict],getattributes={}):
    """
    decorator to autodiscover nested frame descriptions. MUST use 'frameclass=xxxx' notation on decriptor parameters if you change defaults
    :param frameclass:  frame class to descend, or ordered list of classes, if non default.  default is 'dict'
    :param getattributes: callable object to extract a dictionary from the frame class so it can explore it, or dictionary keyed to classes. default is to use 'vars()' if not specifed
    :return:
    """
    def doit(original_class):
        orig_init = original_class.__init__
        orig_iter = original_class.__iter__
        # make copy of original __init__, so we can call it without recursion

        def __init__(self, *args, **kws):
            orig_init(self, *args, **kws) # call the original __init__
            self._dp_iterator=None
            self._dp_priorframes=None
            self._dp_provides=None
            self._dp_ranprovides=False
            self._dp_provideslock=threading.Lock()

        def __iter__(self):
            if not self._dp_ranprovides:
                dummy=self.provides
            if self._dp_iterator!=None:
                i=self._dp_iterator
                pf=self._dp_priorframes
                self._dp_iterator=None
                self._dp_priorframe=None
                if pf!=None:
                    for f in pf:
                        yield f
                for f in i:
                    yield f
            else:
                for f in orig_iter(self):
                    yield f

        original_class.__init__ = __init__ # set the class' __init__ to the new one
        original_class.__iter__ = __iter__
        original_class.provides=property(realprovides(nestedclasses,getattributes,nesting=True,orig_iter=orig_iter))
        return original_class
    if(func==None):
        return doit
    return doit(func)

def autoprovide(func=None,frameclass=dict,getattributes=None):
    """
    decorator to autodiscover frame descriptions. MUST use 'frameclass=xxxx' notation on decriptor parameters if you change defaults
    :param frameclass: frame class to descend, if non default.  default is 'dict'
    :param getattributes: callable object to extract a dictionary from the frame class so it can explore it. default is to use 'vars()' if not specifed
    :return:
    """
    def doit(original_class):
        orig_init = original_class.__init__
        orig_iter = original_class.__iter__
        # make copy of original __init__, so we can call it without recursion

        def __init__(self, *args, **kws):
            orig_init(self, *args, **kws) # call the original __init__
            self._dp_iterator=None
            self._dp_priorframes=None
            self._dp_provides=None
            self._dp_ranprovides=False
            self._dp_provideslock=threading.Lock()

        def __iter__(self):
            if not self._dp_ranprovides:
                dummy=self.provides
            if self._dp_iterator!=None:
                i=self._dp_iterator
                pf=self._dp_priorframes
                self._dp_iterator=None
                self._dp_priorframe=None
                if pf!=None:
                    for f in pf:
                        yield f
                for f in i:
                    yield f
            else:
                for f in orig_iter(self):
                    yield f

        original_class.__init__ = __init__ # set the class' __init__ to the new one
        original_class.__iter__ = __iter__
        original_class.provides=property(realprovides(frameclass,getattributes,nesting=False,orig_iter=orig_iter))
        return original_class
    if(func==None):
        return doit
    return doit(func)


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
