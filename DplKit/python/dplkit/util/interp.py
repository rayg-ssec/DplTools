#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.util.interp
~~~~~~~~~~~~~~~~~~

Interpolation tools


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
from datetime import datetime, timedelta
from operator import itemgetter


LOG = logging.getLogger(__name__)

pool_data = namedtuple('pool_data', 'when data')
pool_poly = namedtuple('pool_poly', 'start end coeffs')




class TimeSeriesPolyInterp(object):
    """
    Piecewise interpolation for order 1 and up for numpy array data on a datetime sequence
    Given a time-ordered series of (datetime, numpy-array) pairs
    maintain a pool of recent values to interpolate between the mid-times

    inputs must consistently have the same shape and type
    times must be monotonic    
    """
    shape = None  # uniform shape of the output
    dtype = None  # dtype of the output
    _order = None
    _pool_lowwater = None
    _pool_highwater = None
    _times = None
    _pool = None   # list of pool_data tuples, at least order+1 long to be useful
    _polys = None  # dict of (start,end) : pool_poly tuples

    def __init__(self, order = 1, pool_high = 64, pool_low = 16):
        self._order = order
        self._pool_highwater = pool_high
        self._pool_lowwater = pool_low
        self._times = []
        self._pool = []  # matches _times
        self._polys = {}
        assert(pool_low > order)
        assert(pool_high > pool_low)

    def _drain(self, no_older_than_this=None):
        "periodically remove polygons from poly-table that no longer are relevant, draining pool from high-mark to low-mark"
        if len(self._pool) > self._pool_highwater:
            del self._pool[:-self._pool_lowwater]
            del self._times[:-self._pool_lowwater]
        if (no_older_than_this is not None) and (len(self._pool)>=self._order):
            n = 0
            while self._times[n] > when:
                n += 1
            del self._times[:n]
            del self._pool[:n]
        if len(self._polys) >= len(self._pool):   
            times = set(x.when for x in self._pool)
            self._polys = dict((k,v) for (k,v) in self._pool.items() if (v.start in times) or (v.end in times))

    @property
    def nan(self):
        """a nan in the shape and type of the data we're interpolating. 
        This property is returned in the case that "input-time not in interpolator"
        We create a new nan-array every time in case downstream likes to mutate output
        """
        if self.shape is None or self.dtype is None:
            raise AssertionError('data cannot be returned prior to data being added')
        if len(self.shape) == 0:
            return np.nan
        norn = np.empty(self.shape, dtype=self.dtype)
        norn[:] = np.nan
        return norn

    def append(self, time_data_tuple):
        """
        Add data to the interpolator in time-increasing order.
        :param time_data_tuple: Pair of (datetime, numpy-array) containing new data.
        """
        when, data = time_data_tuple
        data = np.array(data)
        assert(len(self._pool)==0 or when > self._pool[-1].when)
        if self.shape is None:
            self.shape = data.shape
            self.dtype = data.dtype
        self._pool.append(pool_data(when, data))
        self._times.append(when)  # used for bisect search

    def __iadd__(self, seq):
        """
        Add an iterable, increasing sequence of (datetime, numpy-array) data to the interpolator.
        """
        group = list(pool_data(when,np.array(data)) for (when,data) in seq)
        self._pool += group
        self._times += [item.when for item in group]
        # FUTURE: check that time is ever-increasing i.e. monotonic
        if self.shape is None and self._pool:
            self.shape = self._pool[0].data.shape
            self.dtype = self._pool[0].data.dtype
        return self

    @property
    def span(self):
        if len(self._pool) <= self._order: 
            return None, None
        return self._pool[self._order - 1].when, self._pool[-1].when

    def __contains__(self, when):
        if len(self._pool) <= self._order:
            return False
        start, end = self.span
        # for order > 1, we only allow interpolation between last two segments of a given grouping, to enforce ~continuity
        if (when < start) or (when > end):
            return False
        return True

    def _generate_poly(self, pool_datas):
        "create a polynomial fit curve of order self.order; should work for multidimensional arrays by flattening to columns"
        base = pool_datas[-2].when        
        xs = np.array([(x.when - base).total_seconds() for x in pool_datas])
        # stack data as horizontal columns corresponding to the time offset columns
        ys = np.hstack([q.data.ravel() for q in pool_datas])
        LOG.debug(repr(xs))
        LOG.debug(repr(ys))
        coeffs = np.polyfit(xs, ys, self._order)
        return pool_poly(pool_datas[-2].when, pool_datas[-1].when, coeffs)

    def _apply_poly(self, poly, when):
        s = (when - poly.start).total_seconds()
        col = np.polyval(poly.coeffs, s)
        LOG.debug('s=%f' % s)
        # reshape to match original data
        return col.reshape(self.shape)

    def _poly_for_time(self, when):
        # find the offset within the pool
        assert(len(self._times) == len(self._pool))
        # find index we would insert at, such that everything left of this index is <=when
        dex = bisect.bisect_right(self._times, when)
        # get the time key for the poly we want to use, if it exists in the poly cache
        # any given polynomial only interpolates for the last two time points used to generate it
        key = self._pool[dex].when
        assert(self._pool[dex].when == self._times[dex])
        assert(self._times[dex] > when)
        LOG.debug('found %s before %s @ %d/%d' % (when, key, dex, len(self._times)))
        poly = self._polys.get(key, None)
        if poly is None:  # grab the right block of pool data, e.g. 0:2 for order 1
            poly = self._generate_poly(self._pool[dex - self._order : dex + 1])
            self._polys[poly.end] = poly
            # assert(a.when == poly.start)
        return poly

    def __call__(self, when):
        if when not in self:
            s,e = self.span
            LOG.warning("cannot extrapolate to time %s, coverage is %s ~ %s; returning nans" % (when, s,e))
            return self.nan
        poly = self._poly_for_time(when)
        data = self._apply_poly(poly, when)
        self._drain()
        return data

    def __str__(self):
        pool_entries = len(self._pool)
        polynomials = len(self._polys)
        start, end = self.span
        return """<TimeSeriesPolyInterp with %(pool_entries)d pool entries, %(polynomials)d polynomials, 
        time range %(start)s ~ %(end)s>
        """ % locals()




class testLinearFibonacciInterp(unittest.TestCase):
    """
    guh
    wuh
    fnub
    """
    tspi = 1

    def setUp(self):
        self.tspi = TimeSeriesPolyInterp(order=1)
        self.start = when = datetime.utcnow()
        delta = timedelta(seconds=10)
        t = [when - delta, when]
        y = [1,1]
        for n in range(8):
            y.append(y[-2] + y[-1]) 
            t.append(t[-1] + delta)  # this is okay because it's all integer arithmetic
            print t[-1], y[-1]
        print self.tspi
        print ', '.join(str(x) for x in t)
        print y
        self.tspi += list((a,np.array(b, dtype=np.float32)) for (a,b) in zip(t,y))
        self.reference = dict(zip(t,y))
        self.t = t
        self.y = y
        self.ts = [(x - t[0]).total_seconds() for x in t]
        print str(self.reference)
        self.end = t[-1]

    def testBasics(self):
        assert(self.tspi is not None)
        when = self.start
        while when < self.end:
            q = self.tspi(when)
            print when, q, self.reference[when]
            self.assertEqual(np.round(q), self.reference[when])
            # self.assertTrue(np.abs(q - self.reference[when]) < 0.0005)
            when += timedelta(seconds=20)

    def testPlots(self):
        import matplotlib.pyplot as plt
        t = self.start
        xs = []
        ys = []
        incr = timedelta(seconds=1, microseconds=431539)
        while t < self.end:
            print "++ %s %s~%s" % ( (t, ) + self.tspi.span )
            y = self.tspi(t)
            print t, y
            x = (t - self.t[0]).total_seconds()
            xs.append(x)
            ys.append(y)
            t += incr
        fig = plt.figure()
        ax = plt.axes()
        ax.plot(xs, ys, 'go')
        ax.plot(self.ts, self.y, 'bx-')
        plt.draw()
        plt.title('linear interpolation of fibonacci series')
        fn = '/tmp/interp.png'
        fig.savefig(fn, dpi=200)
        print "wrote " + fn
        return None


class testQuadraticSineInterp(unittest.TestCase):
    """
    Test interpolation of a sine wave, including nan returns in starting segment
    """
    tspi = 1

    def _sin(self, dt):
        x = (dt - self.start).total_seconds() * self.dx
        return x, np.sin(x)

    def setUp(self):
        self.tspi = TimeSeriesPolyInterp(order=2)
        self.start = when = datetime.utcnow()
        N = 17
        self.dx = dx = np.pi*5 / N  # each 1s increment has this much value
        self.x = x = np.array([dx * i for i in range(N)])
        self.y = y = np.sin(x)
        delta = timedelta(seconds=1)
        self.t = t = [(when + delta*i) for i in range(N)]

        self.tspi += [(a,np.array(b)) for (a,b) in zip(t,y)]

        print self.tspi
        self.end = t[-1]

    def testPlots(self):
        import matplotlib.pyplot as plt
        t = self.start
        xs = []
        ys = []
        dy = []
        incr = timedelta(seconds=0, microseconds=131539)
        while t < self.end:
            print "++ %s %s~%s" % ( (t, ) + self.tspi.span )
            y = self.tspi(t)
            print t, y
            rx,ry = self._sin(t)
            xs.append(rx)
            ys.append(y)
            dy.append(y-ry)
            t += incr
        fig = plt.figure()
        ax = plt.axes()
        ax.plot(xs, ys, 'go')
        ax.plot(self.x, self.y, 'bx-')
        ax.plot(xs, dy, 'r-')
        plt.legend(['interp', 'input', 'diff-from-calc'])
        plt.title('quadratic interpolation of sine wave')
        plt.draw()
        fn = '/tmp/interp2.png'
        fig.savefig(fn, dpi=200)
        print "wrote " + fn
        return None




# def suite():
#     suite = unittest.TestSuite()
#     suite.addTest(unittest.makeSuite(testInterp))
#     return suite





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


