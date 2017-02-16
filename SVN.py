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

from subprocess import Popen, PIPE
from sys import platform as _platform

def svn_call(command):
	command_splitted = command.split(" ")
	return svn_call_array(command_splitted)

def svn_call_array(command_array):
	p = Popen(command_array, stdin=PIPE, stdout=PIPE, stderr=PIPE)
	output, err = p.communicate()
	returncode = p.returncode
	return [returncode, output, err]
	
	
def svn_update():
	print "Updating software from SVN (%s)..." % _platform,
	command = []
	if _platform[:5] == "linux":
		command = ["svn", "update"]
	elif _platform[:3] == "win":
		command = ["C:\\Program Files\\TortoiseSVN\\bin\\TortoiseProc.exe", "/path:./", "/command:update", "/closeonend:1"]
	code, output, error = svn_call_array(command)

	if code == 0:
		print "OK."
	else:
		print "Error: %s" % error

def svn_commit():
	print "Committing all changes"
	command = []
	if _platform[:5] == "linux":
		command = ["svn", "commit"]
	elif _platform[:3] == "win":
		command = ["C:\\Program Files\\TortoiseSVN\\bin\\TortoiseProc.exe", "/path:./", "/command:commit", "/closeonend:1"]
	code, output, error = svn_call_array(command)
	

svn_update()
