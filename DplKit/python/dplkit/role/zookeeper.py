#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.role.zookeeper
~~~~~~~~~~~~~~~~~~~~~


A zookeeper is given a logical data query as a URL, match keys, or SQL 'where' expression,
and generates a series of media URI sets which can be used to access the data.
Each set in the sequence is alternate URIs for the same media asset.

query -> [ (media-uri, media-uri, ...), (media-uri, ...) ]

The zookeeper is created one-per-collection.

:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""

import os, sys
import logging

LOG = logging.getLogger(__name__)



class aZookeeper(object):
    """Zookeeper(uri, **constraints) returns an URL when given sets of logical URIs
    """

    def __init__(self, *args, **kwargs):
        """
        """
        super(aZookeeper, self).__init__()
        self.uri = uri

    def __call__(self, uri=None):
        """yields a sqeuence of media uri sets
        """
        pass




def test():
    """ """
    pass


if __name__=='__main__':
    test()
