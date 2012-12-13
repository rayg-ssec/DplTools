#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.test.waveform
~~~~~~~~~~~~~~~~~~~~

Sinusoids and other waveforms as DPL entities


:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""


__author__ = 'R.K.Garcia <rayg@ssec.wisc.edu>'
__revision__ = '$Id:$'
__docformat__ = 'reStructuredText'




import os, sys
import logging, unittest
import numpy as np
from datetime import datetime, timedelta

import dplkit.frame.keys as keys
from dplkit.role.narrator import aNarrator


LOG = logging.getLogger(__name__)

sine_info = {'longname': 'generated test waveform',
             'units': '1'}

class SineNarrator(aNarrator):
    """
    A sine-wave generator capable of multdimensional output using an optional skew array
    """
    period = None
    width = None
    provides = None

    def __init__(self, period=timedelta(seconds=1), width=timedelta(microseconds=123456), start=None, 
                shape=(1,), skew=0.0, wave=np.sin, factor=None, N = None, channel_name='waveform'):
        """
        :param period: timedelta period for the sinusoid
        :param width: timedelta increment for the value of every frame in seconds
        :param start: starting datetime, defaults to current UTC
        :param shape: shape of the output array, defaults to (1,); if skew is an array this is ignored
        :param skew: skew increment scalar, or skew array which is used to offset the x-value going into the wave function
        :param wave: wave function taking a numpy array, defaults to numpy.sin
        :param factor: multiply factor for converting seconds to xvalue, defaults to computing based on period
        :param N: number of frames to return, default None implies unlimited
        """
        self.period = period
        self.width = width
        self.start = start if start is not None else datetime.utcnow()
        if hasattr(skew, 'dtype'):
            shape = skew.shape
        else:
            skew = np.cumsum(np.repeat([skew], np.prod(shape))).reshape(shape)
        self.shape = shape
        self.skew = skew
        self.wave = wave
        if factor is None:
            factor = 2*np.pi / self.period.total_seconds()
        self.factor = factor
        self.channel_name = channel_name
        self.provides = {'start': keys.start, 'width': keys.width, channel_name: sine_info}
        self.N = N

    def __repr__(self):
        return "SineNarrator(period=%(period)r, width=%(width)r, start=%(start)r, shape=%(shape)r, skew=%(skew)r, wave=%(wave)r, factor=%(factor)r, N=%(N)s, channel_name=%(channel_name)r)" % vars(self)

    def __str__(self):
        return "<SineNarrator '%s' from '%r' with period %s width %s>" % (self.channel_name, self.wave, self.period, self.width)

    def read(self, *args, **kwargs):
        when = self.start
        n = self.N
        while (n is None) or (n > 0):
            t = (when - self.start).total_seconds() * self.factor
            x = self.skew + t
            y = self.wave(x)
            frame = {'start': when,
                     'width': self.width,
                     self.channel_name: y, 
                     "_x": t}
            yield frame
            when += self.width
            n -= 1




class testSimple(unittest.TestCase):
    """
    Test interpolation of a sine wave, including nan returns in starting segment
    """

    def setUp(self):
        self.it = SineNarrator(N=512, width=timedelta(microseconds=5000), skew=np.array([0.0, np.pi/2, np.pi]))

    def testPlots(self):
        import matplotlib.pyplot as plt
        frames = list(self.it)
        fig = plt.figure()
        ax = plt.axes()
        xs = np.array([f['_x'] for f in frames])
        ys = np.array([f['waveform'] for f in frames])
        ax.plot(xs, ys)
        plt.title('sine wave')
        plt.draw()
        fn = '/tmp/waveform.png'
        fig.savefig(fn, dpi=200)
        print "wrote " + fn
        return None





def main():
    import optparse
    usage = """
%prog [options] ...


"""
    parser = optparse.OptionParser(usage)
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

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3,options.verbosity)])

    if not args:
        unittest.main()
        return 0


    # FIXME main logic
      
    return 0




if __name__=='__main__':
    sys.exit(main())
