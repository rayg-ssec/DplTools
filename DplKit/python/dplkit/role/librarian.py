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


class AmbiguousQueryError(Exception):
    """Exception saying that a given query doesn't resolve to an un-ambiguous sequence of assets
    """
    pass


class aLibrarian(object):
    """A Librarian returns sets of media asset URIs when given search expressions.
    """
    provides = None  # mapping-of-mappings showing available search keys for the collection, and their metadata
    requires = None  # FUTURE: mapping describing preconditions for a successful search. 

    @property
    def meta(self):
        return self.provides

    def __init__(self, *args, **kwargs):
        """
        """
        super(aLibrarian, self).__init__()

    def query(self, *where_exprs, **key_values):
        """
        Yield time-ordered sequence of dictionaries satisfying search conditions
        Each dictionary should have a 'uri' key compatible with being passed to a zookeeper
        where_exprs is a series of string expressions (SQL-conformant) of which all must be satisfied
        key_values is a dictionary of asset attributes that must match
        key_values can also include lambda expressions returning true/false on the key in question
        Admissible keys should be a subset of librarian's meta.keys().
 
        example for a simple system with one librarian, one zookeeper, one narrator class:

        assets = mylibrarian(start=start_time, end=end_time)
        for asset_info in assets:
            media_info = myzookeeper(**asset_info)
            frames = mynarrator(**media_info)
            for frame in frames:
                process(frame)

        """
        pass

    def __call__(self, *args, **kwargs):
        """
        default action for a librarian is to query()
        """
        return self.query(*args, **kwargs)


def test():
    """ """
    pass


if __name__=='__main__':
    test()
