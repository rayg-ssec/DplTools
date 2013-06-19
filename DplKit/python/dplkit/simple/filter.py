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


if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
