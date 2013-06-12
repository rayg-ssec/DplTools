#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DPLKit frame basics

**Definitions**
Frame: a collection of key-value pairs representing a given time range for an instrument or system of instruments.
       In Python, we represent frames as dictionaries, and less often as namedtuples or object-attribute.
       Frames are always passive data structures (not full objects) and should be readily serialized to allow different representations.
Framestream: a sequence of frames. In Python, we access Framestreams using generator mechanics.
Metaframe: a dictionary with names matching a Frame, with values themselves being dictionaries of object attributes, most often strings.

Elementary frame: A frame representing one "discrete" measurement for an instrument, i.e. only one time-step is included
Compound frame: A frame holding an accumulation of timesteps. Typically has a seconds_offset key

Actor: An object which manipulates framestreams, often acting as source for one framestream and sink for one or more framestreams.

Primary framestream: The framestream which drives the timing of the final output, and which other streams are filtered to conform to.
Clock: A framestream which simply produces start+width timeframes, which can be used to synchronize


"""
