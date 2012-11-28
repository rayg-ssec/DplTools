#!/usr/bin/env python# -*- coding: utf-8 -*-
"""
package.module
~~~~~~~~~~~~~~


A description which can be long and explain the complete
functionality of this module even with indented code examples.
Class/Function however should not be documented here.


:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""


__author__ = 'R.K.Garcia <rayg@ssec.wisc.edu>'
__revision__ = '$Id:$'
__docformat__ = 'reStructuredText'




import os, sys
import logging, unittest


LOG = logging.getLogger(__name__)

class TimeInterpolatedMerge(dplkit.role.resampler):
    """
    take the time frame information from the primary stream, 
    and time-interpolate selecteed channels from the other streams into a composite stream

    This will deliver all frames from the primary. Period. No excuses.
    In the case that one or more of the secondaries cannot provide data, their channels are None.
    """
    def __init__(self, primary, secondary_list, channels=None):
        """
        primary: the framestream that we get time information from
        secondary_list : a collection of secondary framestreams which get merged in order
        channels: optional set() of channel names which get merged from the secondaries
        """
        # examine .meta from primary and each of the secondaries to get list of channels
        # compare against channels-of-interest set if provided to create a table
        # merge meta from primary with meta from secondaries, masked by channels-of-interest
        # set .meta for self
        pass

    def resample(self, *args, **kwargs):
        # for each frame in the primary
        #  see if we have an applicable frame from each of the secondaries
        #  call secondary.next() if we need another frame in order to interpolate
        #  catch StopIteration exception? yes, just return when we encounter StopIteration
        #  time interpolate between neighboring secondary frames, for channels of interest
        #    use simple linear interpolation using frame center times? 
        #    maintain dimensionality in all the arrays in the desired channels
        #  if channels is None, use all channels from the secondary
        #  create a new output frame which merges the primary data with the interpolated secondary data
        #  yield that frame
        pass 



def test1(lidar_info, radar_info):

    lidar = dpl_rti(**lidar_info)
    radar = dpl_rti(**radar_info)

    # does this take start time, time interval, end time?
    # take the time information from the first parameter
    tim = TimeInterpolatedMerge(lidar, [radar])
    merge = MergeStreams([lidar, radar])
    for frame in merge:
        printstuff(frame)

class 





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
