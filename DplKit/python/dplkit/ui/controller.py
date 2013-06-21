#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.ui.controller
~~~~~~~~~~~~~~~~~~~~

DPL UI module for controller objects

These objects act as the main bridge between the GUI/widget and the
DPL stream. Once a stream exists, its data is "bound" to a component
of a widget via the controller's "bind_*" methods.

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

    def _apply_line_x(self, line_object, data_array):
        """Bind method for updating the X data of a line.

        Note: A user should not need to call this method.
        """
        data_array = data_array.squeeze()
        # Get the last dimension
        if data_array.ndim > 1:
            # XXX: Only supports 2D
            data_array = data_array[-1,:]
        line_object.set_xdata(data_array)

    def _apply_line_y(self, line_object, data_array):
        """Bind method for updating the Y data of a line.

        Note: A user should not need to call this method.
        """
        data_array = data_array.squeeze()
        # Get the last dimension
        if data_array.ndim > 1:
            # XXX: Only supports 2D
            data_array = data_array[-1,:]
        line_object.set_ydata(data_array)

    def _apply_line_data(self, line_object, *data_array):
        """Bind method for updating the X and Y data of a line.
        Accepts 1 2D array or 2 1D arrays.
        """
        if len(data_array) == 1:
            data_array = data_array.squeeze()
            if data_array.ndim > 2:
                # XXX: Only supports 3D
                data_array = data_array[-1,:]
            line_object.set_data(data_array)
        else:
            x = data_array[0].squeeze()
            y = data_array[1].squeeze()
            line_object.set_data(x, y)

    def _apply_image_data(self, image_object, data_array):
        """Bind method for updating the 2D data of an image.

        Note: A user should not need to call this method.
        """
        image_object.set_data(data_array)

    def _apply_autolimit(self, ax, tight, scalex, scaley):
        """Bind method for updating the limits of an axis.

        Note: A user should not need to call this method.
        """
        ax.relim()
        ax.autoscale_view(tight=tight, scalex=scalex, scaley=scaley)

    def bind_line_x_to_channel(self, stream_channel_name, line_object=None):
        """Bind a single stream channel to a line's X data.
        """
        if line_object is None:
            raise ValueError("`line_object` is a required argument")
        self.bindings.append( ((stream_channel_name,), partial(self._apply_line_x, line_object)) )

    def bind_line_y_to_channel(self, stream_channel_name, line_object=None):
        """Bind a single stream channel to a line's Y data.
        """
        if line_object is None:
            raise ValueError("`line_object` is a required argument")
        self.bindings.append( ((stream_channel_name,), partial(self._apply_line_y, line_object)) )

    def bind_line_data_to_channel(self, *stream_channel_name, **kwargs):
        """Bind a one or two stream channels to a line's data. If one channel
        is specified it must be a 2D array. If two are specified then they
        should be 1 dimensional; ordered as X then Y.
        """
        line_object = kwargs.get("line_object", None)
        if line_object is None:
            if len(stream_channel_name) == 1:
                raise ValueError("`line_object` is a required argument")
            else:
                line_object = stream_channel_name[-1]
                stream_channel_name = stream_channel_name[:-1]
        self.bindings.append( (stream_channel_name, partial(self._apply_line_data, line_object)) )

    def bind_image_to_channel(self, stream_channel_name, image_object=None):
        """Bind a 2D image stream channel to an image's data.
        """
        if image_object is None:
            raise ValueError("`image_object` is a required argument")
        self.bindings.append( ((stream_channel_name,), partial(self._apply_image_data, image_object)) )

    def bind_axis_autoscale_x(self, axis, interval=1, padding=0.0):
        """Bind autoscaling behavior to the X axis.

        :keyword interval: number of frames between limit updates (default 1)
        :keyword padding: fraction of data range to add to the minimum and maximum limits (default 0)
        """
        count = interval
        scaley = False
        if axis in self.limit_bindings:
            count = self.limit_bindings[axis][1]
            scaley = self.limit_bindings[axis][3]

        axis.set_xmargin(padding)

        # Future: Actually use 'tight'
        binding = (interval, count, True, scaley, partial(self._apply_autolimit, axis, False, True, scaley))
        self.limit_bindings[axis] = binding

    def bind_axis_autoscale_y(self, axis, interval=1, padding=0.0):
        """Bind autoscaling behavior to the X axis.

        :keyword interval: number of frames between limit updates (default 1)
        :keyword padding: fraction of data range to add to the minimum and maximum limits (default 0)
        """
        count = interval
        scalex = False
        if axis in self.limit_bindings:
            count = self.limit_bindings[axis][1]
            scalex = self.limit_bindings[axis][2]

        axis.set_ymargin(padding)

        # Future: Actually use 'tight'
        binding = (interval, count, scalex, True, partial(self._apply_autolimit, axis, False, scalex, True))
        self.limit_bindings[axis] = binding

    def handle_new_frame(self, frame):
        """Method called to handle every new frame from the Stream.
        Only handle's compound dictionary frames or frames where each
        dictionary value is a numpy array.

        Note: Users shouldn't need to call this method themselves. It is
        automatically called when the Stream produces a frame.
        """
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

