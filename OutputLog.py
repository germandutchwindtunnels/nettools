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

import PyQt4.QtGui as QtGui

class OutLog(object):
	"""Outlog enables one to redirect stdout and stderr to a QTextEdit widget. It was shamelessly stolen from: http://stackoverflow.com/questions/17132994/pyside-and-python-logging/17145093#17145093"""
	def __init__(self, edit, out=None, color=None):
		"""(edit, out=None, color=None) -> can write stdout, stderr to a QTextEdit."""
		self.edit = edit
		self.out = out
		self.color = color

	def write(self, m):
		if self.color:
			tc = self.edit.textColor()
			self.edit.setTextColor(self.color)

		self.edit.moveCursor(QtGui.QTextCursor.End)
		self.edit.insertPlainText( m )

		self.edit.ensureCursorVisible()
	
		if self.color:
			self.edit.setTextColor(tc)
	
		if self.out:
			try:
				self.out.write(m)
			except IOError:
				pass
	def flush(self):
		if self.out:
			try:
				self.out.flush()
			except IOError:
				pass
