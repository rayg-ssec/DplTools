#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.simple.resampler
~~~~~~~~~~~~~~~~~~~~~~~


Useful examples of resampling filters


:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""


__author__ = 'R.K.Garcia <rayg@ssec.wisc.edu>'
__revision__ = '$Id:$'
__docformat__ = 'reStructuredText'




import os, sys
import logging, unittest
import bisect
from collections import defaultdict, namedtuple

from ..role.resampler import aResampler # abstract base class for resampler role
from ..frame.struct import as_struct    # allow both dictionary-style and struct-style frames
from ..util.interp import TimeSeriesPolyInterp


LOG = logging.getLogger(__name__)






class TimeInterpolatedMerge(aResampler):
    """
    Using the time frame information from the primary stream, 
    time-interpolate channels from the other streams into a composite stream.

    This will yield all frames from the primary.
    In the case that one or more of the secondaries cannot provide data, their channels are None.
    """
    provides = None 
    requires = None

    _schedule = None  # schedule of what data comes from where, [(channel, source), ...]
    _pool = None # current frames we're using for each source, {source : recent-frame-list, ...}
    _pool_depth = 2  # for now, only allow pools to be 2-points long; later, we allow splining or other fits

    @staticmethod
    def _generate_meta_from_sequence(channel_seq, *sources):
        schedule = list(channel_seq)
        meta = dict( (chn,source.meta[chn]) for (chn,source) in schedule )
        return meta, schedule

    @staticmethod
    def _generate_meta_from_set(channels, *sources):
        schedule = []
        meta = {}
        for source in sources:
            assert(hasattr(source, 'meta'))
            for chn,nfo in source.meta.items():
                if chn in meta:
                    continue
                if (channels is not None) and (chn not in channels):
                    continue
                meta[chn] = nfo
                schedule.append((chn, source))
        return meta, schedule

    def _meta_sequence(*sources):
        for source in sources:
            assert(hasattr(source,'meta'))
            for chn in source.meta.keys():
                yield chn,source

    @staticmethod
    def _generate_meta(channels, *sources):
        """
        return metadata dictionary and transfer schedule using each of the upstream sources
        """
        if channels is not None:
            if hasattr(channels, 'keys'):
                return TimeInterpolatedMerge._generate_meta_from_sequence(channels.items(), *sources)
            elif hasattr(channels, '__contains__'): 
                return TimeInterpolatedMerge._generate_meta_from_set(channels, *sources)
            elif iterable(channels):
                return TimeInterpolatedMerge._generate_meta_from_sequence(channels, *sources)                
            else:
                raise ValueError('channels must be a mappable or set')
        else:
            return TimeInterpolatedMerge._generate_meta_from_sequence(TimeInterpolatedMerge._meta_sequence(*sources))




    def __init__(self, primary, secondary_list, channels=None):
        """
        Initialize a time-interpolated merge filter with one primary and one or more secondary sources.
        Overlapping channels are selected with priority on earlier (primary, then secondaries in order).
        Metaframe for self is updated to merge primary and secondary source metadata.

        :param primary: the framestream that we get time information from
        :param secondary_list : a collection of secondary framestreams which get merged in order
        :param channels: optional set() of channel names which get merged from the secondaries. 
                         If this is a dictionary, the key is the channel name and value is which source to use.
        """
        # examine .meta from primary and each of the secondaries to get list of channels and our .provides dict
        # compare against channels-of-interest set if provided to create a table
        # merge meta from primary with meta from secondaries, masked by channels-of-interest
        # set .meta for self
        self.provides, self._schedule = TimeInterpolatedMerge._generate_meta(channels, primary, *secondary_list)

        LOG.debug('transfer schedule: %s' % repr(self.schedule))
        LOG.debug('what we provide: %s' % repr(list(self.provides.keys())))

        self._pool = defaultdict(list)

    def _frame_intersecting(self, spool, when):
        "return frame from source-pool intersecting a time, or None"


    def _fill_pool_for_source(self, source, when):
        "for a given source, fill its pool until we can cover a timeframe's midpoint"



    def _drain_pool(self, ending_at):
        "remove everything from pool older than ending_at"
        for _,spool in self._pool.items():
            del spool[:-self._pool_depth]





    def resample(self, *args, **kwargs):
        """
        Yield a framestream, one for each timeframe in the primary source.        
        Interpolate the channels provided by secondary sources.
        Channels are returned as None if the identified source of that channel was unavailable.
        """
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

        # for each frame in primary, obtain time window
        # for each channel,source in schedule
        #   check source 

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
