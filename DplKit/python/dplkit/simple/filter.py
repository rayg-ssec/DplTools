#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
package.module
~~~~~~~~~~~~~~


A description which can be long and explain the complete
functionality of this module even with indented code examples.
Class/Function however should not be documented here.


:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""

import os, sys
import logging, unittest
import numpy as np
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from dplkit.role.filter import aFilter


LOG = logging.getLogger(__name__)


class ExplodeCompoundFrameFilter(aFilter):
    """
    Reduce a compound-frame (multiple sample times) to a simple-frame (single sample times)
    """

    def __init__(self, source, **kwargs):
        """
        """
        super(self.__class__, self).__init__(source=source)
        self.provides = dict(source.provides)

    def process(self, *args, **kwargs):
        """the default action of the filter is to process one framestream into another"""
        for frame in self.source:
            whens = frame['start']
            n_simple_frames = len(whens)
            LOG.debug('exploding compound frame into %d simple frames' % n_simple_frames)
            for dex in range(n_simple_frames):
                zult = {}
                for channel_name in self.provides.keys():
                    src = frame[channel_name]
                    zult[channel_name] = src[dex]
                yield zult


class AccumlateSimpleFramesFilter(aFilter):
    """
    Accumulate simple frames to follow a timestream being provided
    """

    def __init__(self, time_source, source, **kwargs):
        """
        :param time_source: time-frame source
        :param source: data-frame source holding only simple (single-timestep) frames
        :param kwargs:
        """
        super(self.__class__, self).__init__(source=source)
        self.provides = dict(source.provides)
        self.time_source = time_source

    def process(self, *args, **kwargs):
        """
        Iterate through time_source
        For each data frame whose start time is within the time-frame, accumulate
        Yield new composite
        """
        gen = iter(self.source)

        def _append(zult, simple_frame):
            for key in self.provides.keys():
                zult[key].append(simple_frame[key])

        frame = next(gen)
        for timeframe in self.time_source:
            zult = defaultdict(list)
            # timeframes are simple, or they should be
            tf_start = timeframe['start']
            tf_stop = timeframe['start'] + timeframe['width']
            n = 0
            try:
                while frame['start'] < tf_start:
                    LOG.debug('discarding simple frame at time %s' % frame['start'])
                    frame = next(gen)
                while frame['start'] < tf_stop:
                    _append(zult, frame)
                    n += 1
                    frame = next(gen)
            except StopIteration as all_done:
                if n:
                    LOG.debug('yielding final compound frame with %d simple frames concatenated' % n)
                    yield dict((k, np.array(v)) for (k, v) in zult.items())
                raise
            if n:
                LOG.debug('yielding compound frame with %d simple frames concatenated' % n)
                yield dict((k, np.array(v)) for (k,v) in zult.items())

class RollingWindowFilter(aFilter):
    """Cache a frame stream for ``window_size`` number of records, yielding
    a frame for each new record. The ``window_size`` only affects the first
    dimension.

    Note that a "windowed" frame is yielded for *each* new record, NOT for
    every ``window_size`` number of records. This is useful when a frame of
    the past N records is wanted (ex. updating GUI).
    """

    def __init__(self, source, **kwargs):
        super(RollingWindowFilter, self).__init__(source, **kwargs)
        self.source = source
        self.cache = {}
            
        # Number of elements in the first dimension to cache
        self.window_size = kwargs.pop("window_size", 1)
        # A subset of the channels provided by the source
        self.channels = kwargs.pop("channels", None)
    
    def init_cache(self, f):
        # FIXME: Could use 'provides' if in source
        channels = f.keys() if self.channels is None else self.channels
        for k in channels:
            # We only support numpy arrays
            if isinstance(f[k], np.ndarray):
                self.cache[k] = np.zeros((self.window_size,) + (np.squeeze(f[k]).shape or (1,)), dtype=f[k].dtype)
                self.cache[k][:] = np.nan
    
    def update_cache(self, f):
        if not self.cache:
            self.init_cache(f)
    
        for k in self.cache.keys():
            # Get our last window
            cached_window = self.cache[k]

            # Roll to the new window location
            cached_window = np.roll(cached_window, -1, axis=0)

            # Add the new data
            if k in f:
                try:
                    cached_window[-1,:] = np.squeeze(f[k])
                except StandardError as e:
                    LOG.warning("%s had a problem adding the data" % (k,))
                    LOG.warning("Cache shape %r, Frame's shape %r" % (cached_window.shape, f[k].shape))
                    data = np.zeros(cached_window.shape[1:], dtype=cached_window.dtype)
                    # FIXME: This won't work if the data is not a float or doesn't support nan
                    data[:] = np.nan
                    cached_window[-1,:] = data
                    raise
            else:
                data = np.zeros(cached_window.shape[1:], dtype=cached_window.dtype)
                # FIXME: This won't work if the data is not a float or doesn't support nan
                data[:] = np.nan
                cached_window[-1,:] = data
            self.cache[k] = cached_window
    
    def process(self, *args, **kwargs):
        for f in self.source:
            self.update_cache(f)
    
            yield self.cache.copy()

class TransposeChannelsFilter(aFilter):
    """Simple filter to transpose any data in a
    compound frame with a "transpose" method. Primarily used for
    numpy arrays.

    Note: Expects compound dictionary frames.
    """
    def __init__(self, source, **kwargs):
        super(TransposeChannelsFilter, self).__init__(source, **kwargs)
        self.source = source

    def process(self, *args, **kwargs):
        """Transpose any channels that have a transpose method.

        Copies incoming frame before tranposing.
        """
        for f in self.source:
            f = f.copy()
            for k in f.keys():
                if hasattr(f[k], "transpose"):
                    f[k] = f[k].transpose()
            yield f

class StructToDict(aFilter):
    """Simple filter to turn struct frames into dictionary frames.

    Note: Will not work on complex frames.
    """
    def __init__(self, source, **kwargs):
        super(StructToDict, self).__init__(source, **kwargs)
        self.source = source

    def process(self, *args, **kwargs):
        for f in self.source:
            # Check for "as_dict" method if frames are instance of dplkit.frame.struct
            if hasattr(f, "as_dict"):
                yield f.as_dict()
            else:
                yield vars(f)

class testOne(unittest.TestCase):
    """
    """

    def setUp(self):
        from dplkit.test.waveform import SineNarrator
        from dplkit.frame.clock import FixedFrameRate
        from datetime import datetime, timedelta

        self.start = nau = datetime.utcnow()
        width = timedelta(microseconds=5000)
        self.a = SineNarrator(N=64, start=nau, width=width, #end=nau+width*64,
                              skew=np.array([0.0, np.pi / 2, np.pi]), channel_name='a')
        self.t = FixedFrameRate(start=nau, interval=width*7, stop=nau+width*100)
        self.b = AccumlateSimpleFramesFilter(self.t, self.a)
        self.c = ExplodeCompoundFrameFilter(self.b)

    def testOne(self):
        for _,frame in zip(range(64),self.c):
            LOG.debug(str(frame['start']))

class TestRollingWindowFilter(unittest.TestCase):
    """Test RollingWindowFilter
    """
    def fake_source(self):
        for i in range(64):
            yield {
                    "value1":np.array([i],dtype=np.float32),
                    "value2":np.array([i],dtype=np.float32),
                    "value3":5
                    }

    def test_basic_1(self):
        """Test basic use case of RollingWindowFilter.
        Ignores non-compound frame channels, but defaults
        to rolling all other channels.
        """
        a = self.fake_source()
        b = RollingWindowFilter(a, window_size=5)
        c = iter(b)

        for frame in c:
            self.assertIn("value1", frame)
            self.assertIn("value2", frame)
            self.assertNotIn("value3", frame)

    def test_basic_2(self):
        """Test basic use case of RollingWindowFilter with specific channels.
        Ignores non-specified channels.
        """
        a = self.fake_source()
        b = RollingWindowFilter(a, window_size=5, channels=["value1"])
        c = iter(b)

        for frame in c:
            self.assertIn("value1", frame)
            self.assertNotIn("value2", frame)
            self.assertNotIn("value3", frame)

class TestStructToDict(unittest.TestCase):
    """Test the StructToDictFilter
    """
    class StructFrame(object):
        """Kind of sad, but we have to make structs before we can
        make them dicts again.
        """
        def __init__(self, dict_f):
            for k,v in dict_f.items():
                setattr(self, k, v)

    def test_basic_struct(self):
        """Test converting generic struct-like frames.
        """
        from dplkit.test.waveform import SineNarrator
        from datetime import datetime, timedelta

        start = nau = datetime.utcnow()
        width = timedelta(microseconds=5000)
        a = SineNarrator(N=64, start=nau, width=width, #end=nau+width*64,
                              skew=np.array([0.0, np.pi / 2, np.pi]), channel_name='a')
        def struct_maker(source):
            for f in source:
                yield self.StructFrame(f)
        b = struct_maker(a)
        c = StructToDict(b)

        for _,frame in zip(range(64),c):
            LOG.debug(str(frame["start"]))

    def test_basic_dplkit_struct(self):
        """Test converting DplKit struct frames.
        Since DplKit struct frames have a special "asdict" method which will
        be used instead of "vars(frame)".
        """
        from dplkit.test.waveform import SineNarrator
        from dplkit.frame.struct import struct
        from datetime import datetime, timedelta

        start = nau = datetime.utcnow()
        width = timedelta(microseconds=5000)
        a = SineNarrator(N=64, start=nau, width=width, #end=nau+width*64,
                              skew=np.array([0.0, np.pi / 2, np.pi]), channel_name='a')
        def struct_maker(source):
            for f in source:
                yield struct(f)
        b = struct_maker(a)
        c = StructToDict(b)

        for _,frame in zip(range(64),c):
            LOG.debug(str(frame["start"]))

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
