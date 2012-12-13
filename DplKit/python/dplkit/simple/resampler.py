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
import numpy as np
from collections import defaultdict, namedtuple


LOG = logging.getLogger(__name__)



class testOne(unittest.TestCase):
    """
    Test interpolation of a sine wave, including nan returns in starting segment
    """

    def setUp(self):
        from dplkit.test.waveform import SineNarrator
        from datetime import datetime, timedelta
        self.start = nau = datetime.utcnow()
        self.a = a = SineNarrator(N=512, start=nau, width=timedelta(microseconds=5000), skew=np.array([0.0, np.pi/2, np.pi]), channel_name='a')
        self.b = b = SineNarrator(N=400, start=nau-timedelta(microseconds=500000), width=timedelta(microseconds=6750), channel_name='b' )
        self.c = c = SineNarrator(N=4, start=nau-timedelta(seconds=1), period=timedelta(seconds=6), width=timedelta(seconds=1), channel_name='c' )
        self.it = TimeInterpolatedMerge(a, [b, c])        

    def testPlots(self):
        import matplotlib.pyplot as plt
        frames = list(self.it)
        assert(512==list(frames))
        x = np.array([(q['start']-self.start).total_seconds() for q in frames])
        def gety(name, frames=frames):
            return np.array([q[name] for q in frames])
        a = gety('a')
        b = gety('b')
        c = gety('c')
        fig = plt.figure()
        ax = plt.axes()
        ax.plot(x,a)
        ax.plot(x,b)
        ax.plot(x,c)
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
