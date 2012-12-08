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
    _order = None
    _max_pool_len = None
    _times = None
    _pool = None   # list of pool_data tuples, at least order+1 long to be useful
    _polys = None  # dict of (start,end) : pool_poly tuples
    _shape = None  # uniform shape of the output

    def __init__(self, order = 1, max_pool_len = 16):
        self._order = order
        self._max_pool_len = max_pool_len
        self._times = []
        self._pool = []  # matches _times
        self._polys = {}

    def _drain(self, no_older_than_this=None):
        "remove polygons from poly-table that no longer are relevant"
        if len(self._pool) > self._max_pool_len:
            del self._pool[:-self._max_pool_len]
            del self._times[:-self._max_pool_len]
        if (no_older_than_this is not None) and (len(self._pool)>=self._order):
            n = 0
            while self._times[n] > when:
                n += 1
            del self._times[:n]
            del self._pool[:n]
        if len(self._polys) > len(self._pool):
            times = set(x.when for x in self._pool)
            self._polys = dict((k,v) for (k,v) in self._pool.items() if (v.start in times) or (v.end in times))

    def append(self, time_data_tuple):
        when, data = time_data_tuple
        data = np.array(data)
        assert(len(self._pool)==0 or when > self._pool[-1].when)
        if self._shape is None:
            self._shape = data.shape
        self._pool.append(pool_data(when, data))
        self._times.append(when)  # used for bisect search

    def __iadd__(self, seq):
        seq = tuple(seq)
        self._pool += list(pool_data(when,np.array(data)) for (when,data) in seq)
        self._times += list(when for (when,data) in seq)
        # FIXME: check that time is ever-increasing i.e. monotonic
        if self._shape is None and self._pool:
            self._shape = self._pool[0].data.shape
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
        return col.reshape(self._shape)

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
            raise ValueError("cannot extrapolate to time %s, coverage is %s ~ %s" % (when, s,e))
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




class testInterp(unittest.TestCase):
    """
    guh
    wuh
    fnub
    """
    tspi = 1

    def setUp(self):
        self.tspi = TimeSeriesPolyInterp(order=2, max_pool_len=64)
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
        fn = '/tmp/interp.png'
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


