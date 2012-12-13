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



# FUTURE: Implement a TimeSeriesRollingMean that has a similar interface to this, 
# which might be useful to pass as an alternative into dplkit.simple.resampler.TimeInterpolatingMerge?? 
# That would be most useful if you're merging a secondary source with a high relative framerate


class TimeSeriesPolyInterp(object):
    """
    Piecewise interpolation for order 1 and up for arbitrary-dimension numpy array data on a datetime sequence.
    Given a time-ordered series of (datetime, numpy-array) pairs,
    maintain a pool of recent values to interpolate between.
    Also generate polynomial fits on-demand, with each polynomial segment using (order+1) 
    data points and interpolating between the last two points.
    If the input time is outside the current pool of data, 
    Pool has a high-water mark and a low-water mark, as data is added it gets drained to the low-water mark when
    the high-water mark is encountered 

    inputs must consistently have the same shape and type
    times must be monotonic    
    """
    shape = None  # uniform shape of the output
    dtype = None  # dtype of the output
    order = None
    _pool_lowwater = None
    _pool_highwater = None
    _times = None
    _pool = None   # list of pool_data tuples, at least order+1 long to be useful
    _polys = None  # dict of (start,end) : pool_poly tuples

    def __init__(self, order = 1, shape=None, dtype=None, pool_high = 64, pool_low = 16):
        """
        :param order: the order of the polynomial to use, e.g. 1 for linear, 2 for quadratic. Implies order+1 points needed.
        :param pool_high: depth the data/polynomial cache can get before it gets drained
        :param pool_low: depth that the cache will get drained to (discarding content earlier in time first) 
        :param shape: shape of the numpy array to be generated (default to using that of first data value)
        :param dtype: dtype of the numpy array to be generated (default to using that of first data value)
        """
        self.shape = shape
        self.dtype = dtype
        self.order = order
        if pool_high <= pool_low: 
            pool_high = 2*pool_low
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
        if (no_older_than_this is not None) and (len(self._pool)>=self.order):
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

    def _conformant(self, data):
        if not hasattr(data, 'dtype') or self.dtype != data.dtype:
            LOG.warning('copying data due to different dtype')
            data = np.array(data, dtype=self.dtype)
        return data

    def append(self, time_data_tuple):
        """
        Add a data point to the interpolator in time-increasing order.
        Data is copied to an internal cache, in order to ensure immutability.
        A ValueError is raised if the data does not match the expected/configured data shape.
        :param time_data_tuple: Pair of (datetime, numpy-array) containing new data.
        """
        when, data = time_data_tuple
        data = np.array(data)
        LOG.debug('adding %s' % when)
        if (len(self._pool)>0) and (when <= self._pool[-1].when): 
            raise ValueError('%s is not greater than %s' % (when, self._pool[-1].when))
        if self.shape is None:
            self.shape = data.shape
            self.dtype = data.dtype
        if self.shape != data.shape:
            raise ValueError('shape does not match configured shape of %r' % self.shape)
        self._pool.append(pool_data(when, data))
        self._times.append(when)  # used for bisect search

    def __iadd__(self, seq):
        """
        Add an iterable, increasing sequence of (datetime, numpy-array) data to the interpolator.
        Data is copied to an internal cache, in order to ensure immutability.
        :param seq: an iterable sequence of (datetime, numpy-array) pairs
        """
        group = list(pool_data(when, np.array(data)) for (when,data) in seq)
        self._pool += group
        self._times += [item.when for item in group]
        # FUTURE: check that time is ever-increasing i.e. monotonic, n
        if self.shape is None and self._pool:
            self.shape = self._pool[0].data.shape
            self.dtype = self._pool[0].data.dtype
        return self

    @property
    def span(self):
        """
        The (start, end) timespan currently available to interpolate data.
        """
        if len(self._pool) <= self.order: 
            return None, None
        return self._pool[self.order - 1].when, self._pool[-1].when

    def __contains__(self, when):
        """
        Return whether a given datetime can be interpolated. If this routine returns False, expect NaNs to be returned.
        """
        if len(self._pool) <= self.order:
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
        ys = np.vstack([q.data.ravel() for q in pool_datas])
        LOG.debug(repr(xs))
        LOG.debug(repr(ys))        
        coeffs = np.polyfit(xs, ys, self.order)
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
        LOG.debug('need polynomial ending at index %d' % dex)
        LOG.debug(repr(self._times))
        key = self._pool[dex].when
        assert(self._pool[dex].when == self._times[dex])
        assert(self._times[dex] > when)
        LOG.debug('found %s before %s @ %d/%d' % (when, key, dex, len(self._times)))
        poly = self._polys.get(key, None)
        if poly is None:  # grab the right block of pool data, e.g. 0:2 for order 1
            poly = self._generate_poly(self._pool[dex - self.order : dex + 1])
            self._polys[poly.end] = poly
            # assert(a.when == poly.start)
        return poly

    def __call__(self, when):
        """
        Interpolate data to a given time, returning a properly-sized NaN array in the case that it's outside the active span.
        Piecewise interpolation is done such that for order O, an (O+1)-value piece is used, with the requested time fitting 
        within the last two times of the piece.

        Polynomials are generated as needed and cached, in case the data is only needed sparsely.

        In the case that no valid pieces are available in the cache, an array of like-shaped NaNs is returned.
        You can test the available timespan using .span or "time in object" syntax (i.e. __contains__)

        :param when: a datetime object such that  .span[0] <= when <= .span[1]
        """
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


