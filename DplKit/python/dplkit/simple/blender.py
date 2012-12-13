#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.simple.blender
~~~~~~~~~~~~~~~~~~~~~



:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""

import os, sys
import logging, unittest
import bisect
import numpy as np
from collections import defaultdict, namedtuple

from dplkit.role.blender import aBlender # abstract base class, enforces .combine mainly
from dplkit.frame.struct import as_struct    # allow both dictionary-style and struct-style frames
from dplkit.util.interp import TimeSeriesPolyInterp
import dplkit.frame.keys as keys

LOG = logging.getLogger(__name__)



class Merge(aBlender):
    def __init__(self, *sources, **kwargs):
        super(Merge, self).__init__()
        self._sources = sources

    def combine(self, *args, **kwargs):
        from ..frame.struct import struct
        for framegroup in zip(self._sources):
            f = struct(framegroup[0])
            for q in framegroup[1:]:
                vars(f).update(vars(q))
            yield f




def center_time(data):
    "extract start-time, time-width, and center-time from a struct-like frame; or start,None,start if no width provided"
    start = data.start   # ref dplkit.frame.keys
    width = getattr(data, 'width', None)
    t = start if (width is None) else (start + width/2)
    return start, t, width


# we use these, we provide these, these aren't numpy arrays so let's not interpolate them.
# we can't make assumptions about other channels unless we have standardization of type metadata in .meta / .provides
# the primary alternative is to use the channel specification / dictionary on initialization
# FUTURE: find a more elegant way to handle this
INTERP_VERBOTEN_CHANNELS = set(['start', 'width'])


# FUTURE: this should also conform to aBlender?

class TimeInterpolatedMerge(aBlender):
    """
    Using the time frame information from the primary stream, 
    time-interpolate channels from the other streams into a composite stream.

    This will yield all frames from the primary.
    In the case that one or more of the secondaries cannot provide data, their channels are None.
    """
    provides = None 
    requires = None

    _schedule = None  # schedule of what data comes from where, [(channel, source), ...]
    _iters = None   # dictionary of { source: function-fetching-next-frame }
    _tsips = None   # interpolator dictionary { channel: TimeSeriesPolyInter}
    _primary = None
    _consumed = None  # bookkeeping information on how many frames consumed from each source

    @staticmethod
    def _generate_meta_from_sequence(channel_seq, channels_ignore, *sources):
        schedule = list((chn,source) for (chn,source) in channel_seq if chn not in channels_ignore)
        meta = dict( (chn,source.meta[chn]) for (chn,source) in schedule )
        return meta, schedule

    @staticmethod
    def _generate_meta_from_set(channels, channels_ignore, *sources):
        schedule = []
        meta = {}
        for source in sources:
            assert(hasattr(source, 'meta'))
            for chn,nfo in source.meta.items():
                if chn in meta or chn in channels_ignore:
                    continue
                if (channels is not None) and (chn not in channels):
                    continue
                meta[chn] = nfo
                schedule.append((chn, source))
        return meta, schedule

    @staticmethod
    def _meta_sequence(*sources):
        chnset = set()
        for source in sources:
            assert(hasattr(source,'meta'))
            for chn in source.meta.keys():
                if chn not in chnset:
                    LOG.debug('%s from %s' % (chn,source))
                    yield chn,source
                chnset.add(chn)

    @staticmethod
    def _generate_meta(channels, channels_ignore, *sources):
        """
        return metadata dictionary and transfer schedule using each of the upstream sources
        """
        if channels is not None:
            if hasattr(channels, 'keys'):
                return TimeInterpolatedMerge._generate_meta_from_sequence(channels.items(), channels_ignore,  *sources)
            elif hasattr(channels, '__contains__'): 
                return TimeInterpolatedMerge._generate_meta_from_set(channels, channels_ignore, *sources)
            elif iterable(channels):
                return TimeInterpolatedMerge._generate_meta_from_sequence(channels, channels_ignore, *sources)                
            else:
                raise ValueError('channels must be a mappable or set')
        else:
            return TimeInterpolatedMerge._generate_meta_from_sequence(TimeInterpolatedMerge._meta_sequence(*sources), channels_ignore)


    def __init__(self, primary, secondary_list, channels=None, order=1, pool_depth=16, allow_nans=False, channels_ignore=None):
        """
        Initialize a time-interpolated merge filter with one primary and one or more secondary sources.
        Overlapping channels are selected with priority on earlier (primary, then secondaries in order).
        Metaframe for self is updated to merge primary and secondary source metadata.
        Update order is preserved such that primary is always updated first, followed by secondaries in order.

        :param primary: the framestream that we get time information from
        :param secondary_list : a collection of secondary framestreams which get merged in order
        :param channels: optional set() of channel names which get merged from the secondaries. 
                         If this is a dictionary, the key is the channel name and value is which source to use.
        :param order: polynomial order to use for interpolating, defaults to 1 (see dplkit.util.interp.TimeSeriesPolyInterp)
        :param pool_depth: how many recent values to keep in cache for individual channels

        """
        # examine .meta from primary and each of the secondaries to get list of channels and our .provides dict
        # compare against channels-of-interest set if provided to create a table
        # merge meta from primary with meta from secondaries, masked by channels-of-interest
        # set .meta for self
        secondary_list = list(secondary_list)
        if channels_ignore is None:
            channels_ignore = INTERP_VERBOTEN_CHANNELS
        self.provides, self._schedule = TimeInterpolatedMerge._generate_meta(channels, channels_ignore, primary, *secondary_list)

        self.provides['start'] = keys.start
        self.provides['width'] = keys.width

        self._iters = dict((source, iter(source)) for source in [primary] + secondary_list)

        LOG.debug('transfer schedule: %s' % self._schedule)
        LOG.debug('what we provide: %s' % repr(list(self.provides.keys())))

        self._primary = primary
        self._tsips = dict((channel, TimeSeriesPolyInterp(order=order, pool_low=pool_depth)) for (channel,_) in self.provides.items())
        self._allow_nans = allow_nans  # FIXME, use this
        self._consumed = defaultdict(int)


    def _eat_next_frame(self, source, data = None):
        "append new data from a source to the interpolator objects, returning the new time-span we can interpolate within"
        # self._integrity_check()
        LOG.debug('eating frame from %s' % source)
        if data is None:
            it = self._iters[source]
            try:
                data = it.next()
            except StopIteration:
                # FIXME: if this throws a StopIteration, we have a secondary source that ran out of track
                # we should let the interpolator for the source's channels generate nans for everything from here on out
                LOG.warning('source %s is out of data, future version should handle this by providing NaNs for this source' % source)
                raise
                LOG.debug(repr(data))
            data = as_struct(data)
        start, t, width = center_time(data)
        LOG.debug('using frame center time of %s' % (t))
        # collect inner time-span of all the TSIPs to return as guidance, and push the channel data into the interpolators
        s,e = None, None
        for channel,sched_source in self._schedule: 
            tsip = self._tsips[channel]  # FUTURE: merge this into schedule
            if source is sched_source:
                # assert(channel in source.provides)   should already be guaranteed in schedule creation
                LOG.debug('appending channel data to interpolator for %s' % (channel))
                tsip.append((t, getattr(data, channel)))
            # track the available time period for the current tsips
            ts,te = tsip.span
            if (ts is not None) and ((s is None) or (s < ts)): 
                s = ts
            if (te is not None) and ((e is None) or (e > te)): 
                e = te
        self._consumed[source] += 1
        return s,e 


    def _frame_at_time(self, when):
        "return a dictionary frame for a given datetime"
        zult = {}
        for (channel, source) in self._schedule:
            tsip = self._tsips[channel]  # FUTURE: merge into _schedule?
            s,e = tsip.span
            if (s is not None) and (when < s): 
                if self._allow_nans:
                    LOG.warning('time %s is outside the interpolation realm %s ~ %s, expect NaNs for %s' % (when, s,e,channel))
                else:
                    raise ValueError("out-of-order input sequence? cannot interpolate %s before %s (attempted %s)" % (channel, s, when))
            while (e is None) or (when > e):
                LOG.debug('feeding frame of data to %s interpolator and its siblings, waiting for %s' % (channel, when))
                s,e = self._eat_next_frame(source)
                LOG.debug('can now interpolate %s %s ~ %s' % (channel, s, e))

            # perform time interpolation
            zult[channel] = tsip(when)
        return zult

    def _integrity_check(self):
        # integrity check schedule
        for (chn,source) in self._schedule:
            print "checking %s" % chn
            assert(chn in source.meta)


    def combine(self, *args, **kwargs):
        """
        Yield a framestream of dictionaries, one for each timeframe in the primary source.        
        Interpolate the channels provided by secondary sources.
        Use dplkit.frame.struct.as_struct() adapter if struct-like frames are preferred.
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

        # self._integrity_check()

        for timeframe in self._iters[self._primary]:
            LOG.debug('timeframe: %s' % timeframe)
            timeframe = as_struct(timeframe)
            self._eat_next_frame(self._primary, timeframe)
            start, when, width = center_time(timeframe)
            # FUTURE: should this be part of schedule?
            zult = self._frame_at_time(when)
            zult['start'] = start
            zult['width'] = width
            zult['_center_time'] = when    #FUTURE: is this advisable? useful? 
            yield zult




# def test1(lidar_info, radar_info):

#     lidar = dpl_rti(**lidar_info)
#     radar = dpl_rti(**radar_info)

#     # does this take start time, time interval, end time?
#     # take the time information from the first parameter
#     tim = TimeInterpolatedMerge(lidar, [radar])
#     merge = MergeStreams([lidar, radar])
#     for frame in merge:
#         printstuff(frame)


class testOne(unittest.TestCase):
    """
    Test interpolation of a sine wave, including nan returns in starting segment
    """

    def setUp(self):
        from dplkit.test.waveform import SineNarrator
        from datetime import datetime, timedelta
        self.start = nau = datetime.utcnow()
        self.a = a = SineNarrator(N=512, start=nau, width=timedelta(microseconds=5000), period=timedelta(microseconds=175114), skew=np.array([0.0, np.pi/2, np.pi]), channel_name='a')
        self.b = b = SineNarrator(N=4500, start=nau-timedelta(microseconds=63000), period=timedelta(microseconds=400000), width=timedelta(microseconds=16750), channel_name='b')
        self.c = c = SineNarrator(N=6, start=nau-timedelta(seconds=1), period=timedelta(seconds=3), width=timedelta(microseconds=250000), channel_name='c')
        assert(c.channel_name == 'c')
        self.it = TimeInterpolatedMerge(a, [b, c])

    def testPlots(self):
        import matplotlib.pyplot as plt
        frames = list(self.it)
        print len(frames)
        # assert(512==list(frames))
        from pprint import pprint
        pprint(list(self.it._consumed.items()))
        x = np.array([(q['start']-self.start).total_seconds() for q in frames])
        def gety(name, frames=frames):
            return np.array([q[name] for q in frames])
        a = gety('a')
        b = gety('b')
        c = gety('c')
        fig = plt.figure()
        ax = plt.axes()
        ax.plot(x,a, '.')
        ax.plot(x,b, '.')
        ax.plot(x,c, '.')
        plt.grid()
        plt.legend(['a1', 'a2', 'a3', 'b', 'c'])
        plt.title('linear time interpolation test')
        plt.draw()
        fn = '/tmp/resampler.png'
        fig.savefig(fn, dpi=200)
        print "wrote " + fn
        return None








def main():
    import optparse
    usage = """
%prog [options] ...


"""
    parser = optparse.OptionParser(usage)
    parser.add_option('-t', '--test', dest="self_test",
                    action="store_true", default=False, help="run self-tests")
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=3,
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
        unittest.main()
        return 0
        # parser.error( 'incorrect arguments, try -h or --help.' )
        # return 1

    # FIXME main logic
      
    return 0





if __name__=='__main__':
    sys.exit(main())