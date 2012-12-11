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


start = { 'longname' : "datetime.datetime object expressing the start time of a frame",
          'shortname' : 'start',
          'type' : datetime.datetime
          'units' : 'time'
          }

# We prefer start + width, since most instruments will have a constant span, and that's one less thing to compute.
width = { 'longname' : "datetime.timedelta object representing the width of a frame, such that start <= T < (start + width); typically frames have either width or end but not both",
          'shortname' : 'width',
          'type': datetime.timedelta,
          'units' : 'time'
          }

end = { 'longname' : "datetime.datetime object representing the end of a frame, such that start <= T < end; typically frames should either have width or end but not both",
          'shortname' : 'end',
          'type': datetime.datetime,
          'units' : 'time'
          }

is_rolling = { 'longname' : 'whether or not this frame represents a rolling view of the input; if not present assume False'
            'shortname': 'is_rolling',
            'type': bool,
            'units': 'boolean'
            }






def test():
    """ """
    pass


if __name__=='__main__':
    test()
