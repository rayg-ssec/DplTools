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

LOG = logging.getLogger(__name__)


class aBridge(object):
    """
    abstract bridge base. 
    Outgoing bridges act like artists; incoming bridges act like narrators.

    """
    provides = None   # mapping of inforamtion about the framestream channels that will be available
    requires = None   # FUTURE

    def 



#
## Code goes here.
#


def test():
    """ """
    pass


if __name__=='__main__':
    test()
