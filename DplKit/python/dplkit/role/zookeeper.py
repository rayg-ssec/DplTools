#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.role.zookeeper
~~~~~~~~~~~~~~~~~~~~~


A zookeeper is given a logical data query as a URL, match keys, or SQL 'where' expression,
and generates a series of media URI sets which can be used to access the data.
Each set in the sequence is alternate URIs for the same media asset.

Zookeepers typically have nothing to do with framestreams.

query -> [ (media-uri, media-uri, ...), (media-uri, ...) ]

The zookeeper is created one-per-collection.

:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""

import os, sys
import logging
from abc import ABCMeta, abstractmethod

LOG = logging.getLogger(__name__)



class aZookeeper(object):
    """Zookeeper(uri, **constraints) returns an URL when given sets of logical URIs
    """    
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        """
        """
        super(aZookeeper, self).__init__()
        self.uri = uri

    @abstractmethod
    def capture(self, uri, *args, **kwargs):
        """yields a sequence of dictionaries including 'url' key and other metadata useful as criteria
        """
        pass

    # def guide(self, uri):
    #     """higher-level optional API yields a sequence of tuples:
    #     (asset-metadata-mapping, narrator-creating-callable)
    #     Typically a user would 
    #         - review the metadata-mapping content to see if it's of interest
    #         - if it's of interest, use the corresponding callable with no parameters to obtain a narrator
    #     """
    #     # FUTURE: a Broker role to identify which narrator class to use based on zookeeper locate output()
    #     pass

    def open(self, uri):
        """
        Return a file object (or equivalent as expected by the client) for a given URI.
        This may use whatever means are necessary to fetch the media, and may cache it.        
        The object returned is typically read-only
        """
        raise NotImplementedError("open is not supported from this collection")

    def __call__(self, *args, **kwargs):
        """
        default action of the zookeeper is to capture media as immediately usable URLs
        """
        return self.capture(*args, **kwargs)





def test():
    """ """
    pass


if __name__=='__main__':
    test()
