#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dplkit.ui.widgets
~~~~~~~~~~~~~~~~~~

DPL UI module for holding pre-built widget classes

"""
__docformat__ = "restructuredtext en"

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import os
import sys
import logging

LOG = logging.getLogger(__name__)

class MplWidget(FigureCanvasQTAgg):
    """A Qt widget for matplotlib plotting.

    Matplotlib widget that can handle blitting. A lot of the blitting logic
    was based off of matplotlib's Animate class, but it did not work properly
    for me during testing. The most significant change is that I save/copy the
    bbox of the entire figure instead of individual axes. A lot of the original
    logic is commented out of the code, but not removed in case of future
    issues with other operating systems or versions of Qt4/matplotlib.
    """
    def __init__(self, blit=False, figure_kwargs=None):
        """The keyword arguments in the `figure_kwargs` keyword
        dictionary are passed to the figure initialization, but should be not
        needed due to Qt available methods for changing size.
        """
        figure_kwargs = figure_kwargs or {} # Don't create mutable defaults
        # Matplotlib's base figure class assigns `self.figure = figure`
        # this is redundant, just in case the base class changes
        self.figure = Figure(**figure_kwargs)
        super(MplWidget, self).__init__(self.figure)

        self._blit = blit
        self._have_run_setup = False

        self._limits_changed = False

    def _init_draw(self):
        """Initialize blit drawing canvas.
        Clear everything off the axes that will need to be redrawn:
            - lines
            - TODO
        Then draw the 'empty' canvas, take a snapshot (copy bbox).
        """
        if not self._blit:
            self._draw()

        # Do initial draw of things on the canvas
        self._draw()

        # Remove lines and such (just hide them)
        for a in self._drawn_artists:
            a.set_visible(False)

        # Redraw everything without the above
        self._draw()

        # Take a snapshot of this
        self._blit_cache[self.figure] = self.copy_from_bbox(self.figure.bbox)
        for a in self._drawn_artists:
            self._blit_cache[a.axes] = self.copy_from_bbox(a.axes.bbox)

        # Put the removed stuff back on
        for a in self._drawn_artists:
            a.set_visible(True)

    def _pre_draw(self):
        if self._blit:
            self._blit_clear(self._drawn_artists, self._blit_cache)

    def _draw(self):
        # the actual canvas draw method
        return super(MplWidget, self).draw()

    def _post_draw(self):
        if self._blit and self._drawn_artists:
            self._blit_draw(self._drawn_artists, self._blit_cache)
        else:
            self.draw_idle()

    def draw(self):
        """Reimplement matplotlib's draw() method to allow blitting.

        Similar approach to matplotlib's Animate class.
        """
        if not self._blit:
            return self._draw()

        if not self._have_run_setup:
            self._have_run_setup = True
            self._setup()
            if self._blit:
                self._setup_blit()

        # If the limits were changed in some way we need to re-copy blitting stuff
        if self._limits_changed:
            self._limits_changed = False
            self._init_draw()
            self._post_draw()
            return

        self._pre_draw()
        #self._draw() # Update any lines here if we were copying Animate
        self._post_draw()

    def add_artist(self, a):
        """Tell the widget that this artist always changes so we need to
        redraw it every time.

        This differs from matplotlib's Animate class in that we are not
        subclassing and requiring a list of artists that changed to be
        provided. We assume that all lines are redrawn. This method lets
        user's tell us any additional artists.
        """
        self._drawn_artists.append(a)

    def resizeEvent(self, event):
        super(MplWidget, self).resizeEvent(event)
        
        if self._blit:
            # Blitting needs to retake it's snapshots if resized
            self._handle_resize()

    # The rest of this code was modified from matplotlib's Animate class
    #     <mpl root>/lib/matplotlib/animation.py
    # The rest of the code in this class is to facilitate easy blitting
    def _blit_draw(self, artists, bg_cache):
        # Handles blitted drawing, which renders only the artists given instead
        # of the entire figure.
        #updated_ax = []
        if self.figure not in bg_cache:
            bg_cache[self.figure] = self.copy_from_bbox(self.figure.bbox)
        for a in artists:
            # If we haven't cached the background for this axes object, do
            # so now. This might not always be reliable, but it's an attempt
            # to automate the process.
            #if a.axes not in bg_cache:
            #    bg_cache[a.axes] = self.copy_from_bbox(a.axes.bbox)
            a.axes.draw_artist(a)
            #updated_ax.append(a.axes)

        # After rendering all the needed artists, blit each axes individually.
        #for ax in set(updated_ax):
        #    self.blit(ax.bbox)
        self.blit(self.figure.bbox)

    def _blit_clear(self, artists, bg_cache):
        # Get a list of the axes that need clearing from the artists that
        # have been drawn. Grab the appropriate saved background from the
        # cache and restore.
        #print bg_cache.keys()
        #axes = set(a.axes for a in artists)
        self.restore_region(bg_cache[self.figure], bbox=self.figure.bbox)
        #for a in axes:
        #    a.figure.canvas.restore_region(bg_cache[a])
        #    #self.restore_region(bg_cache[a], bbox=self.figure.bbox)

    def _setup(self):
        """Method run when things are first starting to gather information
        about how the user set the figure up.
        """
        # Attach callbacks to handle limit changes
        for ax in self.figure.axes:
            ax.callbacks.connect('xlim_changed', self._handle_limits_change)
            ax.callbacks.connect('ylim_changed', self._handle_limits_change)

    def _setup_blit(self):
        """Gather information for blitting to work properly.
        """
        # Setting up the blit requires: a cache of the background for the
        # axes
        self._blit_cache = dict()
        #self._drawn_artists = []
        # XXX: We assume we're only doing lines, this could be an over-simplification
        # Incomprehensible list comprehensions
        self._drawn_artists = [ line_obj for ax in self.figure.axes for line_obj in ax.lines ]

        # Must setup the artists with their renderers, initial draw before we
        # copy anything
        self._init_draw()

        # Clear off any lines at the start
        self._post_draw()

    def _handle_limits_change(self, ax):
        """Handle any axes limits changing.
        This flag is handled in the `draw()` method by redrawing if the limits
        were changed.
        """
        self._limits_changed = True

    def _handle_resize(self):
        #self._blit_cache.clear()
        self._init_draw()
        self._post_draw()

