#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
package.module
~~~~~~~~~~~~~



librarian(search-terms) -> asset-uris


:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""

import os, sys
import logging

LOG = logging.getLogger(__name__)



class aLibrarian(object):
    """A Librarian returns sets of media URIs given search expressions.
    """
    meta = None  # dictionary of available search keys for the collection

    def __init__(self, *args, **kwargs):
        """
        """
        super(aLibrarian, self).__init__()

    def __call__(self, *where_exprs, **key_values):
        """return sqeuence of asset URIs matching search conditions
        where_exprs is a series of string expressions (SQL-based) of which all must be satisfied
        key_values is a dictionary of asset attributes that must match, and can include lambda expressions returning true/false

        example:
        uri_seq = librarian(date = lambda x: (x >= mindate) and (x < maxdate))
        """
        pass

    def where(self, where_expr):
        pass

    def having(self, **key_values):
        pass



def test():
    """ """
    pass


if __name__=='__main__':
    test()
