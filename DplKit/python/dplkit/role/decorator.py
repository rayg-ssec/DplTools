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

class thing(object):
    def __init__(self,fieldname,initval=None):
        self.initvalue=initval
        self.fieldname=fieldname

    def __get__(self, obj, type=None):
        if not hasattr(obj,self.fieldname):
            return self.initval.copy()
        return getattr(obj,self.fieldname)

    def __set__(self, obj, value):
        setattr(obj,self.fieldname,value)

    def __delete__(self, obj):
        delattr(obj,self.fieldname)


def has_provides(cls):
    cls.meta = property(meta)
    if not hasattr(cls,'provides'):
        cls.provides = thing('__p_provides')
    else:
        raise 'already have provides!'
    return exposes_attrs_in_chain(['provides'])(cls)


def has_requires(cls):
    if not hasattr(cls,'requires'):
        cls.requires = thing('__p_requires')
    else:
        raise 'already has requires!'
    return exposes_attrs_in_chain(['requires'])(cls)

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
            print 'locking',self,realme,realme.nestedclasses,realme.getattributes
            self._dp_provideslock.acquire()
            print 'locked',self,realme,realme.nestedclasses,realme.getattributes
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
                #print 'got',self._dp_provides
                self._dp_ranprovides=True
            print 'unlocking',self,realme,realme.nestedclasses,realme.getattributes
            self._dp_provideslock.release()
            print 'unlocked',self,realme,realme.nestedclasses,realme.getattributes
        return self._dp_provides

def autoprovidenested(func=None,nestedclasses=[dict],getattributes={}):
    """
    decorator to autodiscover nested frame descriptions. MUST use 'frameclass=xxxx' notation on decriptor parameters if you change defaults
    :param nestedclasses:  frame class to descend, or ordered list of classes, if non default.  default is 'dict'
    :param getattributes: callable object to extract a dictionary from the frame class so it can explore it, or dictionary keyed to classes. default is to use 'vars()' if not specifed
    :return:
    """
    def doit(original_class):
        orig_init = original_class.__init__
        orig_iter = original_class.__iter__
        # make copy of original __init__, so we can call it without recursion

        def __init__(self, *args, **kws):
            self._dp_iterator=None
            self._dp_priorframes=None
            self._dp_provides=None
            self._dp_ranprovides=False
            self._dp_provideslock=threading.Lock()
            self._dp_randummy=False
            orig_init(self, *args, **kws) # call the original __init__

        def __iter__(self):
            if not self._dp_randummy:
                self._dp_randummy=True
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
            self._dp_iterator=None
            self._dp_priorframes=None
            self._dp_provides=None
            self._dp_ranprovides=False
            self._dp_provideslock=threading.Lock()
            self._dp_randummy=False
            orig_init(self, *args, **kws) # call the original __init__

        def __iter__(self):
            if not self._dp_randummy:
                self._dp_randummy=True
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

#these are exposed class wide, not per instance
def exposes_attrs_in_chain(exposed_attrs):
    class attribute_list(object):
        def __init__(self,klass,fieldname,value):
            self.originalval=value
            self.superval=None
            self.value=list(value)
            if hasattr(klass,fieldname):
                sv=getattr(klass,fieldname)
                if isinstance(sv,tuple):
                    self.superval=sv
                elif isinstance(sv,self.__class__):
                    self.superval=sv.value
                else:
                    raise RuntimeError('Field '+fieldname+' of class (or superclass thereto) '+repr(klass)+' already set to non attribute_list value. is a '+repr(type(sv)))
                for f in self.superval:
                    if f not in self.value:
                        self.value.append(f)
            self.value=tuple(self.value)
            print 'class',klass,'exposes fields',self.value

        def __get__(self,otherself,type=None):
            return self.value

    def decorator(cl):
        cl.___exposed_attrs = attribute_list(cl,'___exposed_attrs',exposed_attrs)
        return cl
    return decorator

def exposes_attrs_of_field(fieldname):
    """
    decorator to allow class instances to return attributes of one of its fields, where the name is not already assigned
    :param fieldname: name of the attribute field which we should source attributes from if not already defined
    :param fieldname:
    :return:
    """
    def decorator(cl):
        oldcget = getattr(cl, '__getattribute__', None)
        if oldcget==None:
            print cl,"isn't a new 'object' type class. FIX IT!"
            raise RuntimeError

        def _getattr_(self, name):
            #if oldcget is not None:
            try:
                return oldcget(self, name)
            except AttributeError as e:
                if name.startswith('_') or (self.___exposed_attrs_child!=None and name not in self.___exposed_attrs_child):
                    raise
                #print "getting",fieldname
                try:
                    if not hasattr(self,fieldname):
                        #print self,"doesn't have",fieldname
                        raise e #don't let this have any chance to go recursive
                    source = getattr(self, fieldname)
                    #print 'getattr recursively returning',name,'of',fieldname,'(',source,')','from',self
                    return getattr(source, name)
                except:
                    raise e

 
        def exposed_deep(self):#returns exposed attributes for all lower exposed features, or None if someone doesn't, thus exposes all
            source = self.__getattribute__(fieldname)
            #print 'exd'
            if not hasattr(source,'___exposed_attrs_all'):
                return None#all are exposed below us
            else:
                return source.___exposed_attrs_all #return all of what the child exposes

        def exposed_all(self):#union of deep and what this exposes (if defined), or None if this doesn't say
            #print 'exa'
            if not hasattr(self,'___exposed_attrs') or self.___exposed_attrs==None:
                return None #at this level, all are exposed. lower, maybe not
            r=self.___exposed_attrs_child
            if r==None:
                return None
            if self.__exposed_attrs==None:
                return None
            r.extend(self.___exposed_attrs)
            return r

        cl.___exposed_attrs_all = property(exposed_all)
        cl.___exposed_attrs_child = property(exposed_deep)
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
