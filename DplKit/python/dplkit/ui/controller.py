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
        self.binding_idx = 0

    def apply_line_x(self, line_object, data_array):
        line_object.set_xdata(data_array)

    def apply_line_y(self, line_object, data_array):
        line_object.set_ydata(data_array)

    def bind_line_x_to_channel(self, stream_channel_name, line_object=None):
        if line_object is None:
            raise ValueError("`line_object` is a required argument")
        self.bindings.append( ((stream_channel_name,), partial(self.apply_line_x, line_object)) )

    def bind_line_y_to_channel(self, stream_channel_name, line_object=None):
        if line_object is None:
            raise ValueError("`line_object` is a required argument")
        self.bindings.append( ((stream_channel_name,), partial(self.apply_line_y, line_object)) )

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

        # Redraw the widget (only needed for matplotlib images)
        if isinstance(self.widget, self._need_redraw):
            self.widget.draw()

