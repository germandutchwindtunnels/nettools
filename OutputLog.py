#/usr/bin/env python
#
# Copyright (C) 2016-2017 DNW German-Dutch Wind Tunnels
#
# This file is part of nettools.
# Nettools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Nettools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with nettools.  If not, see <http://www.gnu.org/licenses/>.
""" This module provides the OutLog class. """

import PyQt4.QtGui as QtGui


class OutLog(object):
    """ Outlog enables one to redirect stdout and stderr to a QTextEdit widget. """

    def __init__(self, edit, out=None, color=None):
        """ (edit, out=None, color=None) -> can write stdout, stderr to a QTextEdit. """
        self.edit = edit
        self.out = out
        self.color = color

    def write(self, msg):
        """ Write a message to output and QTextEdit. """
        if self.color:
            txt_color = self.edit.textColor()
            self.edit.setTextColor(self.color)

        self.edit.moveCursor(QtGui.QTextCursor.End)
        self.edit.insertPlainText(msg)

        self.edit.ensureCursorVisible()

        if self.color:
            self.edit.setTextColor(txt_color)

        if self.out:
            try:
                self.out.write(msg)
            except IOError:
                pass

    def flush(self):
        """ Flush output. """
        if self.out:
            try:
                self.out.flush()
            except IOError:
                pass
