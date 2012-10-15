#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.frame.keys
~~~~~~~~~~~~~~~~~

"standard" keys / channel-names which are used in dplkit

Where useful we re-use names in the CF convention.
http://cf-pcmdi.llnl.gov/documents/cf-standard-names/

:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""

import os, sys
import logging
import datetime

LOG = logging.getLogger(__name__)


start = dict( longname = "datetime object expressing the start time of a frame",
              type = datetime.datetime 
              )

width = dict( longname = "timedelta object representing the width of a frame, such that start <= T < (start + width)"
              type = datetime.timedelta
              )






def test():
    """ """
    pass


if __name__=='__main__':
    test()
