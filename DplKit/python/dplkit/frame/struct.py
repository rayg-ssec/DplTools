#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.frame.struct
~~~~~~~~~~~~~~~~~~~

Depending on circumstances, it's useful to represent frames as 
mappings (like dictionaries with keys) or as 
structures (like objects with attributes/fields). 

This provides a semi-efficient way to go between the two.

Note that this works best if frames are treated as immutable once yielded downstream.


:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""

import os, sys
import logging

LOG = logging.getLogger(__name__)

class struct(object):
    """
    Ingest a mapping (dictionary syntax) as a data struct object (attribute syntax),
    optionally convert back to a new dictionary including any changes.
    Used primarily for DPL framestreams: 
        both data dictionary and data struct are useful in difference circumstances.
    """
    meta = None    # mapping describing the channels available in this frame, typically assigned by the narrator

    @staticmethod
    def from_dict(mapping):
        "create a struct from a mapping / dictionary"
        return struct(mapping=mapping)

    def __init__(self, mapping = None, **kwargs):
        "create from a mapping or another object's attributes"
        if hasattr(mapping, '__getitem__'):
            self._data_ = mapping
        else:
            self._data_ = vars(mapping)
        for k,v in kwargs.items():
            setattr(self, k, v)
        if 'meta' in self._data_ and 'meta' not in kwargs:
            self.meta = self._data_['meta']


    def __getattr__(self, name):        
        if name not in self._data_:
            LOG.debug('invalid name requested from dict2workspace object, must be in %r' % tuple(self._data_.keys()))
            raise NameError('%s not in frame' % name)
        q = self._data_[name]
        setattr(self, name, q)
        return q

    def __str__(self):
        return str(self.as_dict())

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        """
        return as a new dictionary
        """
        dv = dict(self._data_)
        sv = dict((k,v) for (k,v) in vars(self).items() if not (k.startswith('_') and k.endswith('_')))
        dv.update(sv)
        return dv

frame = struct


def test():
    """ """
    pass


if __name__=='__main__':
    test()
