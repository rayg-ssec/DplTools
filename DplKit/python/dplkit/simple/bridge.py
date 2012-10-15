#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.simple.bridge
~~~~~~~~~~~~~~~~~~~~


Example bridge code, using a socket or pipe to provide frames as a series of pickled dictionaries.


:copyright: 2012 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""

import os, sys
import logging
import ctypes as C
from cPickle import loads, dumps, HIGHEST_PROTOCOL

from ..role.bridge import aBridge
from ..frame.struct import struct

LOG = logging.getLogger(__name__)


class header(C.BigEndianStructure):
    _fields_ =  [ ("bytes", C.c_uint64),    # number of bytes in the frame, including the size bytes themselves
                  ("kind", C.c_char * 8)    # null-padded type code for the payload
                ]

HEADER_SIZE = C.sizeof(header)

KIND_META = "metapckl"  # dictionary of metadata about the framestream
KIND_DATA = "datapckl"  # frame data


class FramePicklingBridge(aBridge):
    """
    A bridge which sends/receives a series of pickled frame dictionaries, with 16-byte header.
    Upon initialization, reads metadata dictionary if incoming, and initializes .provides attribute.
    Upon initialization, sends metadata dictionary if outgoing.

    """
    provides = None
    requires = None

    _recv = None    # callable, recv(numbytes)
    _send = None    # callable, send(buffer)
    _source = None  # if sending, this should be upstream generator

    def _next_frame(self):
        hdr_buffer = self._recv(HEADER_SIZE)
        if len(hdr_buffer)==0: 
            return None, None
        hdr = header.from_buffer_copy(hdr_buffer)
        payload_buffer = self._recv(hdr.bytes - HEADER_SIZE)
        return str(hdr.kind), loads(payload_buffer)

    def _send_dict(self, payload, kind=KIND_DATA):
        hdr = header()
        buf = dumps(payload, HIGHEST_PROTOCOL)
        hdr.bytes = len(buf) + HEADER_SIZE
        hdr.kind = kind
        self._send(hdr)
        self._send(buf)

    def __init__(self, recv=None, send=None, source=None, *args, **kwargs):
        self._recv = recv
        self._send = send
        self._source = source

        if recv is not None:
            kind, meta = self._next_frame()
            print repr(kind), repr(meta)
            assert(kind==KIND_META)
            self.provides = meta
        elif send is not None:
            self._send_dict(source.meta, KIND_META)

    def read(self, *args, **kwargs):
        while True:
            kind, payload = self._next_frame()
            if kind==KIND_DATA:
                yield struct(payload, meta=self.provides)
            elif kind==KIND_META:
                self._set_meta(payload)
            elif kind==None:
                raise StopIteration()
            else:
                LOG.warning('unknown kind: %s, ignoring' % kind)

    def process(self, *args, **kwargs):
        assert(self._source is not None)
        for frame in self._source:
            if isinstance(frame, struct):
                it = frame
                self._send_dict(it.as_dict(without_meta = True))
            else:
                it = struct(frame)
                self._send_dict(it.as_dict(without_meta = True))
            yield frame


class _test_source(object):
    meta = {'q': dict(longname = 'a q'), 'r': dict(longname = 'an r')}
    def __iter__(self):
        for q in range(32):
            yield dict(q = q, r = 4*q, meta=self.meta)

def _test_sink(source, fout):
    for each in source:
        print '> ' + repr(each)
        sys.stdout.flush()
    # from time import sleep
    # sleep(2.0)
    fout.close()



def test():
    """ """
    from threading import Thread
    r,w = os.pipe()
    rpipe, wpipe = os.fdopen(r, 'rb', 0), os.fdopen(w, 'wb', 0)  # 0 buffer size
    outgoing = FramePicklingBridge(send=wpipe.write, source=_test_source())
    incoming = FramePicklingBridge(recv=rpipe.read)
    # start up a sending thread
    tid = Thread(target=_test_sink, args=(outgoing.process(), wpipe))
    tid.start()
    # then receive in this thread
    for frame in incoming.read():
        print '< ' + ', '.join('%s=%s' % (k, getattr(frame, k)) for k in incoming.provides.keys() )
        sys.stdout.flush()


if __name__=='__main__':
    test()
