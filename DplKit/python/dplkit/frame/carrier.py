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

LOG = logging.getLogger(__name__)

class carrier(object):
    """enclose a mappable (dictionary syntax) in a data carrier object (attribute syntax)
    optionally convert back to a new dictionary including any changes
    used primarily for DPL framestreams: both data dictionary and data carrier are useful
    """
    def __init__(self, mapping):
        "create from a mapping or another object's attributes"
        if hasattr(mapping, '__getitem__'):
            self._data = mapping
        else:
            self._data = vars(mapping)

    def __getattr__(self, name):
        if name not in self._data:
            LOG.debug('invalid name requested from dict2workspace object, must be in %r' % tuple(self._data.keys()))
            raise NameError('%s not in frame' % name)
        q = self._data[name]
        setattr(self, name, q)
        return q

    def as_dict(self):
        """return a new dictionary
        """
        dv = dict(self._data)
        sv = dict((k,v) for (k,v) in vars(self).items() if not k.startswith('_'))
        dv.update(sv)
        return dv

    def __str__(self):
        return str(self.as_dict())

    def __repr__(self):
        return repr(self.as_dict())



def test():
    """ """
    pass


if __name__=='__main__':
    test()
