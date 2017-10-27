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
"""This is a small wrapper around the auto updating API"""

import sys

sys.path.append("./dulwich")

import dulwich.porcelain as porcelain  # pylint: disable=import-error
import dulwich.errors  # pylint: disable=import-error
from subprocess import check_call as run

github_url = "https://github.com/germandutchwindtunnels/nettools.git"
target_dir = "./"

if len(sys.argv) < 2:
    print "Usage: %s script script-args" % sys.argv[0]
    sys.exit(-1)

try:
    porcelain.pull(target_dir, github_url)
except dulwich.errors.NotGitRepository:
    porcelain.clone(github_url, target_dir)

cmd = sys.executable + " " + " ".join(sys.argv[1:])
run(cmd, shell=True)
