#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
package.module
~~~~~~~~~~~~~



librarian(search-criteria) -> [asset-uri, asset-uri...]


:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""

import os, sys
import logging
from exceptions import Exception

LOG = logging.getLogger(__name__)


class AmbiguousQuery(Exception):
    """Exception saying that a given query doesn't resolve to an un-ambiguous sequence of assets
    """
    pass


class aLibrarian(object):
    """A Librarian returns sets of media asset URIs when given search expressions.
    """
    meta = None  # dictionary of available search keys for the collection

    def __init__(self, *args, **kwargs):
        """
        """
        super(aLibrarian, self).__init__()

    def __call__(self, *where_exprs, **key_values):
        """
        Yield time-ordered sequence of non-overlapping asset URIs satisfying search conditions
        where_exprs is a series of string expressions (SQL-conformant) of which all must be satisfied
        key_values is a dictionary of asset attributes that must match
        key_values can also include lambda expressions returning true/false on the key in question
        Admissible keys should be a subset of librarian's meta.keys().
 
        examples:
        uri_seq = librarian(date = lambda x: (x >= mindate) and (x < maxdate))
        """
        pass



def test():
    """ """
    pass


if __name__=='__main__':
    test()
