#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.ui.controller
~~~~~~~~~~~~~~~~~~~~

DPL UI module for controller objects

"""
__docformat__ = "restructuredtext en"

from PyQt4 import QtCore
from .widget import MplWidget

import os
import sys
import logging
from functools import partial

LOG = logging.getLogger(__name__)

class GUIController(QtCore.QObject):
    """A mediator between a GUI QWidget and the Stream produced frames.
    Controls how the data from the frame gets entered into a widget.

    FUTURE: Add more methods for different widget bindings
    FUTURE: Add binding methods for controlling widgets (buttons, checkboxes)
    FUTURE: Add logic to auto update axis limits (controller or mplwidget?)
        FUTURE: Add logic to only update axis limits every X number of steps (subclass of mplwidget?)
    """
    _need_redraw = (MplWidget,)

    def __init__(self, stream, widget, parent=None):
        super(GUIController, self).__init__(parent)
        self.widget = widget
        self.stream = stream
        self.stream.frame_ready.connect(self.handle_new_frame)

        # Each element in bindings is a 2-element tuple
        # The first is a tuple of the channel names to get data from
        # The second is a callable that expects only the arrays of data for the channels listed in the first element
        self.bindings = []

        # Each element in limit_bindings is a 5-element tuple
        # The key is the axis object involved
        # The first is an interval (when interval data updates have happened, then update)
        # The second is a count up to interval
        # The third is a boolean of whether the X-axis is autoscaled
        # The fourth is a boolean of whether the Y-axis is autoscaled
        # The fifth is a callable that expects no arguments
        self.limit_bindings = {}

    def apply_line_x(self, line_object, data_array):
        line_object.set_xdata(data_array)

    def apply_line_y(self, line_object, data_array):
        line_object.set_ydata(data_array)

    def apply_autolimit(self, ax, tight, scalex, scaley):
        ax.relim()
        ax.autoscale_view(tight=tight, scalex=scalex, scaley=scaley)

    def bind_line_x_to_channel(self, stream_channel_name, line_object=None):
        if line_object is None:
            raise ValueError("`line_object` is a required argument")
        self.bindings.append( ((stream_channel_name,), partial(self.apply_line_x, line_object)) )

    def bind_line_y_to_channel(self, stream_channel_name, line_object=None):
        if line_object is None:
            raise ValueError("`line_object` is a required argument")
        self.bindings.append( ((stream_channel_name,), partial(self.apply_line_y, line_object)) )

    def bind_axis_autoscale_x(self, axis, interval=1, padding=0.0):
        count = interval
        scaley = False
        if axis in self.limit_bindings:
            count = self.limit_bindings[axis][1]
            scaley = self.limit_bindings[axis][3]

        axis.set_xmargin(padding)

        # Future: Actually use 'tight'
        binding = (interval, count, True, scaley, partial(self.apply_autolimit, axis, False, True, scaley))
        self.limit_bindings[axis] = binding

    def bind_axis_autoscale_y(self, axis, interval=1, padding=0.0):
        count = interval
        scalex = False
        if axis in self.limit_bindings:
            count = self.limit_bindings[axis][1]
            scalex = self.limit_bindings[axis][2]

        axis.set_ymargin(padding)

        # Future: Actually use 'tight'
        binding = (interval, count, scalex, True, partial(self.apply_autolimit, axis, False, scalex, True))
        self.limit_bindings[axis] = binding

    def handle_new_frame(self, frame):
        # Put the proper frame data into the widget
        for channel_names,callable in self.bindings:
            channel_values = [ frame.get(channel_name, None) for channel_name in channel_names ]
            if None in channel_values:
                LOG.error("Expected channel %s in frame" % (channel_names[channel_values.index(None)],))
                raise ValueError("Expected channel %s in frame" % (channel_names[channel_values.index(None)],))
            else:
                try:
                    # Update the widget object bound to this channel
                    callable(*channel_values)
                except StandardError:
                    LOG.error("Could not update widget object", exc_info=True)
                    raise

        # If we have any auto-limiting going on then do that now
        for ax,limit_info in self.limit_bindings.items():
            interval,count,scalex,scaley,callable = limit_info
            count += 1
            if count >= interval:
                count = 0
                try:
                    callable()
                except StandardError:
                    LOG.error("Could not autoscale widget object", exc_info=True)
            limit_info = (interval,count,scalex,scaley,callable)
            self.limit_bindings[ax] = limit_info

        # Redraw the widget (only needed for matplotlib images)
        if isinstance(self.widget, self._need_redraw):
            self.widget.draw()

