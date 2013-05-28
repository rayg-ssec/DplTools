#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.ui.main
~~~~~~~~~~~~~~

DPL UI module for holding tests and scripting capabilities

See other UI modules for more details.
"""
__docformat__ = "restructuredtext en"

from PyQt4 import QtGui

from .widget import *
from .stream import *
from .controller import *

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
        for i in range(1,1000):
            #f = { "sine_value" : numpy.sin(x + i/10.0) }
            # Slowly rising sine wave
            f = { "sine_value" : numpy.sin(x + i/10.0)+(i*0.01) }
            yield f

    # Create the DPL Stream
    s         = Stream(test_iterator(), delay=0.1)
    # For debug purposes:
    #s.frame_ready.connect(print_slot)

    # Set up the widget (we could do this in a subclass if this is to be repeated
    #my_widget = MplWidget(blit=False)
    my_widget = MplWidget(blit=True, figure_kwargs=dict(figsize=(4,4)))
    fig       = my_widget.figure
    ax        = fig.add_subplot(111)
    x         = numpy.linspace(0,2*numpy.pi,1024)
    line      = ax.plot(x, numpy.zeros(1024))[0] # only 1 line was created
    ax.set_title("Sine Wave Example - gui_test_1")
    ax.set_xlabel("X Axis")
    ax.set_ylabel("Y Axis")
    ax.grid()

    # Create the controller that handles communication between stream and widget
    control   = GUIController(s, my_widget)
    control.bind_line_y_to_channel("sine_value", line)
    control.bind_axis_autoscale_y(ax, interval=10, padding=0.5)

    my_widget.show()
    print "Starting Stream..."
    s.start()
    print "Exec'ing"
    app.exec_()
    print "Done exec'ing, stopping stream..."
    s.stop()
    print "Waiting for stream..."
    s.wait()
    print "Done waiting for stream thread"
    
def main():
    from argparse import ArgumentParser
    description = """Test DPL UI tools"""
    parser = ArgumentParser(description=description)
    parser.add_argument("--doctest", dest="doc_test", default=False, action="store_true",
            help="Run document tests")
    parser.add_argument("-t", dest="test_name", default=None,
            help="Specify a test function name to run")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)
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

