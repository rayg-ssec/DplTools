#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.metadata.keys
~~~~~~~~~~~~~~~~~~~~

Common / universal search keys with explanation metadata
FUTURE: include a 'validate' key which includes a callable returning true/false, probably made from a regex

:copyright: 2013 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""

__author__ = 'R.K.Garcia <rayg@ssec.wisc.edu>'
__revision__ = '$Id:$'
__docformat__ = 'reStructuredText'

import os, sys
import logging, unittest

LOG = logging.getLogger(__name__)

KEYS = { K_TIME_SPAN, K_BOUNDING_BOX, K_PERIMETER_POLYGON, K_CONTENT_CONVENTION,
         K_COLLECTION_NAME, K_INSTRUMENT, K_SITE, K_EXPERIMENT, K_CONTACT, K_FILE_FORMAT,
         K_FILENAME, K_UUID, K_SOURCE_UUID }

#
## FIXME code goes here.
#

K_TIME_SPAN = ts = time_span = {
    'longname': 'time span in UTC time for data, separated by commas with optional space',
    'convention': 'ISO8601',
    'examples': ('2006-09-20T13:15:44.155, 2006-09-20T13:45:46.214', )
}

K_BOUNDING_BOX = bb = bounding_box = {
    'longname': 'latitude-longitude bounding box for data, normalized to -180..180E or 0..360 if spanning antimeridian',
    'convention': 'WKT',
    'examples': ('POLYGON ((-77.2 38.8, -77 38.8, -77 39, -77.2 39.9, -77.2 38.8))', )
}

K_PERIMETER_POLYGON = pp = perimeter_polygon = {
    'longname': 'latitude-longitude data perimeter, normalized to -180..180E or 0..360E if spanning antimeridian',
    'convention': 'WKT',
    'examples': ('POLYGON ((-77.2 38.8, -77 38.8, -77 39, -77.2 39.9, -77.2 38.8))', )
}

K_CONTENT_CONVENTION = cc = content_convention = {
    'longname': 'convention name that the data is stored according to',
    'convention': None,
    'examples': ('doe_arm', 'jpss_cdfcb')
}

K_COLLECTION_NAME = cn = collection_name = {
    'longname': 'logical identifier of dataset, independent of format and convention, separated by commas if more than one',
    'convention': None,
    'examples': ('sdr,radiance', 'l1c', 'phy_edr,profile')
}

K_INSTRUMENT = inst = instrument = {
    'longname': 'instrument or software system which generated the original data',
    'convention': None,
    'examples': ('shis', 'aeri', 'nasti', 'cris', 'ahsrl')
}

K_SITE = site = {
    'longname': 'site or platform name where the data was recorded - where the instrument was situated',
    'convention': None,
    'examples': ('barrow', 'globalhawk', 'ssec')
}

K_EXPERIMENT = experiment = {
    'longname': 'experiment that the data was taken as part of',
    'convention': None,
    'examples': ('hs3', 'arm')
}

K_CONTACT = contact = {
    'longname': 'contact email regarding the dataset',
    'convention': 'mailto',
    'examples': ('shis-data@ssec.wisc.edu',)
}

K_FILE_FORMAT = ff = file_format = {
    'longname': 'file format of data, typically expressed as an extension',
    'convention': 'extension',
    'examples': ('nc', 'h5', 'hdf', 'fbf')
}

K_FILENAME = fn = filename = {
    'longname': 'filename of the data minus any directory components',
    'convention': 'filename',
    'examples': ('mydata.h5', )
}

K_UUID = uu = uuid = {
    'longname': 'universally unique identifier of the data asset',
    'convention': 'uuid',
    'examples': ('b5695b99-3f58-4f50-b531-c24b504de014', )
}

K_SOURCE_UUID = suu = source_uuid = {
    'longname': 'universally unique identifier/s of the irreplaceable progenitor dataset/s this asset derives from and represents, comma-separated',
    'convention': 'uuid',
    'examples': ('26ee696b-0125-4839-9001-d51707ea4cef, 24e68b31-107c-400b-827f-654b40390104', )
}




def main():
    import optparse
    usage = """
%prog [options] ...
"""
    parser = optparse.OptionParser(usage)
    parser.add_option('-t', '--test', dest="self_test",
                    action="store_true", default=False, help="run self-tests")
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    # parser.add_option('-o', '--output', dest='output',
    #                 help='location to store output')
    # parser.add_option('-I', '--include-path', dest="includes",
    #                 action="append", help="include path")
    (options, args) = parser.parse_args()

    # make options a globally accessible structure, e.g. OPTS.
    global OPTS
    OPTS = options

    if options.self_test:
        unittest.main()
        return 0

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3,options.verbosity)])

    if not args:
        parser.error( 'incorrect arguments, try -h or --help.' )
        return 1

    # FIXME main logic

    return 0


if __name__=='__main__':
    sys.exit(main())
