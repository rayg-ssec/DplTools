#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.ui.__init__
~~~~~~~~~~~~~~~~~~

DPL subpackage for creating Graphical User Interfaces

"""
__docformat__ = "restructuredtext en"

from PyQt4 import QtCore,QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import os
import sys
import logging
from time import sleep
from functools import partial

LOG = logging.getLogger(__name__)

class MplWidget(FigureCanvasQTAgg):
    """A Qt widget for matplotlib plotting.

    FUTURE: Override `draw()` method to use blitting
    """
    def __init__(self, figure_kwargs=None):
        """The keyword arguments in the `figure_kwargs` keyword
        dictionary are passed to the figure initialization, but should be not
        needed due to Qt available methods for changing size.
        """
        figure_kwargs = figure_kwargs or {}
        # Matplotlib's base figure class assigns `self.figure = figure`
        # this is redundant, just in case the base class changes
        self.figure = Figure(**figure_kwargs)
        super(MplWidget, self).__init__(self.figure)

class _StreamThread(QtCore.QThread):
    """Patched QThread object.
    Some older versions of PyQt4 don't have QThread default to calling
    exec_() in the thread's run method.

    The call to exec_() is needed to start the event loop of this thread,
    allowing signals/slots to work properly.
    """
    def run(self):
        self.exec_()

class _StreamObject(QtCore.QObject):
    """Object that holds the code performed by the `Stream` object in the
    new thread.
    """
    finished = QtCore.pyqtSignal()
    frame_ready = QtCore.pyqtSignal(object)

    def __init__(self, iterable=None, callable=None, parent=None,
            delay=None):
        super(_StreamObject, self).__init__(parent)

        if iterable is not None and callable is not None:
            raise ValueError("Either an iterable or a callable should be provided not both")
        elif iterable is not None:
            self.iterable = iterable
            self.callable = None
        else:
            self.iterable = None
            self.callable = callable

        self.delay = delay if delay is None else float(delay)

    def run(self):
        """Iterate through the iterable and signal when new frames are ready.
        """
        # If we were given a callable get the iterable
        if self.iterable is None:
            try:
                self.iterable = self.callable()
            except StandardError:
                self.finished.emit()
                raise

        # Iterate over the stream and signal each new frame
        try:
            for frame in self.iterable:
                self.frame_ready.emit(frame)

                # If the user added artificial delay
                if self.delay is not None: sleep(self.delay)

        except StandardError:
            raise
        finally:
            self.finished.emit()

class Stream(QtCore.QObject):
    """An object encapsulating a DPL stream for use in a GUI.
    A `Stream` takes the provided iterable and provides each element
    via a Qt Signal. This iteration happens in a separate Qt Thread to
    not block the GUI thread. A `Stream` expects the iterable to provide
    a DPL frame (as a python dictionary), although this object may work
    with any object type.

    A Qt Application must be initialized before using a `Stream` so that
    signals and thread communication operates properly.

    FUTURE: Add a Stream subclass (or other) that can be configured by the
            GUI (text boxes, buttons, checkboxes, etc.). Will probably need
            a new type of controller or something.
    """
    # Classes used
    _stream_object_class = _StreamObject
    _stream_thread_class = _StreamThread

    def __init__(self, iterable=None, callable=None, parent=None,
            delay=None,
            exit_app_on_complete=False):
        """Initialize a stream object.
        Allocate a QThread handle, but don't start it. An iterable or
        callable can be provided and will be iterated over in the separate
        thread. If an iterable is provided it will be passed to the new
        thread and iterated over once the `start` method is called. If a
        callable is provided it will be call with no arguments in the new
        thread's affinity once the `start` method is called.

        :keyword iterable: iterator or generator or other iterable object
        :keyword callable: function that returns an interable object
        :keyword parent: Qt parent, read Qt documentation for more info
                         http://pyqt.sourceforge.net/Docs/PyQt4/qobject.html#QObject
        :keyword exit_app_on_complete: Set to true if you want the entire
                         QApplication (including GUI) to exit when this Stream
                         is done processing. Should only be used for testing
                         or in the rare case that no GUI is involved.
        :keyword delay: Add an artificial delay between each iteration (in seconds)
        """
        super(Stream, self).__init__(parent)
        self.thread_handle = self._stream_thread_class()
        self.worker        = self._stream_object_class(
                iterable=iterable,
                callable=callable,
                delay=delay
                )
        self.exit_app_on_complete = exit_app_on_complete

        self._connect_worker_to_thread()

    def _connect_worker_to_thread(self):
        """Connect signals between the worker object and the thread.
        """
        # First move the object to the thread's affinity
        self.worker.moveToThread(self.thread_handle)

        # Make it so the thread dies when the worker is done
        self.worker.finished.connect(self.thread_handle.quit)

        # Make it so the worker starts when the thread starts
        self.thread_handle.started.connect(self.worker.run)

        # If the user is using the stream by itself (no GUI) then
        # they probably want the app to stop exec when the Stream finishes
        if self.exit_app_on_complete:
            self.thread_handle.finished.connect(QtGui.qApp.exit)

        # Make workers frame ready signal public
        self.frame_ready = self.worker.frame_ready

    def start(self):
        self.thread_handle.start()

    def wait(self, msecs=None):
        if msecs is not None:
            return self.thread_handle.wait(msecs=msecs)
        else:
            return self.thread_handle.wait()

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
        self.bindings = []
        self.binding_idx = 0

    def apply_line_x(self, line_object, data_array):
        line_object.set_ydata(data_array)

    def bind_line_y_to_channel(self, stream_channel_name, line_object=None):
        if line_object is None:
            raise ValueError("`line_object` is a required argument")

        # Each element in bindings is a 2-element tuple
        # The first is a tuple of the channel names to get data from
        # The second is a callable that expects only the arrays of data for the channels listed in the first element
        self.bindings.append( ((stream_channel_name,), partial(self.apply_line_x, line_object)) )

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

def basic_test_1():
    """Simple test that prints each value produced by a iterator.
    Should print 0, 1, 2 with a print out of the frame received by a
    test slot.  It should exit cleaning with no other messages.

    This is a good test to see if your threads are starting and stopping
    correctly.
    """
    from pprint import pprint

    # The 'False' means don't even try to open a GUI application, there is no point
    app = QtGui.QApplication([" "], False)

    def test_slot(frame):
        print "Received: ",
        pprint(frame)

    def test_iterator():
        for x in range(3):
            f = {"test_value":x}
            print "Sent:     ",
            pprint(f)
            yield f

    s = Stream(test_iterator(), exit_app_on_complete=True, delay=1.5)
    s.frame_ready.connect(test_slot)
    # Start the other thread for the stream to iterate in
    s.start()

    # Start the main event loop so signals work properly
    app.exec_()

    # This is redundant because we know that the stream quit the app
    # So if the thread died properly this should return immediately
    s.wait()

def basic_test_2():
    pass

def gui_test_1():
    """Simple test that creates a sine wave DPL stream and plots it
    on a line plot.
    """
    import numpy
    from pprint import pprint

    app = QtGui.QApplication([" "])

    def print_slot(frame):
        print "Received: ",
        pprint(frame)

    def test_iterator():
        # Definitely not optimal solution
        # Mimics DPL stream
        x = numpy.linspace(0,2*numpy.pi,1024)
        #for i in range(1,10):
        for i in range(1,2000):
            f = { "sine_value" : numpy.sin(x + i/10.0) }
            yield f

    # Create the DPL Stream
    s         = Stream(test_iterator(), delay=0.5)
    # For debug purposes:
    #s.frame_ready.connect(print_slot)

    # Set up the widget (we could do this in a subclass if this is to be repeated
    my_widget = MplWidget()
    fig       = my_widget.figure
    ax        = fig.add_subplot(111)
    x         = numpy.linspace(0,2*numpy.pi,1024)
    line      = ax.plot(x, numpy.zeros(1024))[0] # only 1 line was created
    ax.set_title("Sine Wave Example - gui_test_1")
    ax.set_xlabel("X Axis")
    ax.set_ylabel("Y Axis")
    ax.set_ylim(-1, 1)

    # Create the controller that handles communication between stream and widget
    control   = GUIController(s, my_widget)
    control.bind_line_y_to_channel("sine_value", line)

    my_widget.show()
    print "Starting Stream..."
    s.start()
    print "Exec'ing"
    app.exec_()
    print "Done exec'ing"
    
def main():
    from argparse import ArgumentParser
    description = """Test DPL UI tools"""
    parser = ArgumentParser(description=description)
    parser.add_argument("--doctest", dest="doc_test", default=False, action="store_true",
            help="Run document tests")
    parser.add_argument("-t", dest="test_name", default=None,
            help="Specify a test function name to run")
    args = parser.parse_args()

    if args.doc_test:
        import doctest
        doctest.testmod()
        return 0
    elif args.test_name is not None:
        return globals()[args.test_name]()
    else:
        parser.print_help()

if __name__ == "__main__":
    sys.exit(main())

