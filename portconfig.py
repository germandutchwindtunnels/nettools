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
""" This file provides basic functionality for patchport configuration """

import sys
import socket

from Cisco import CiscoTelnetSession
from Cisco import CiscoSet


my_fqdn = socket.getfqdn()
main_hostname = socket.gethostname()
dns_domain = my_fqdn[len(main_hostname):]
telnet_port = 23

# Patchlist stuff
patchlist_patchid_column = "Patchnr"

# Init global vars
main_patchnumber = None
main_vlanname = None
main_username = None
main_password = None
switchlist = None


def print_list(thelist):
    """ Concatenate a list of items """
    thelist_str = [str(x) for x in thelist]
    output = '\n'.join(thelist_str)
    print output


def connect_to_switch(hostname, port, username, password):
    """ Connect to a switch and return the session """
    session = CiscoTelnetSession()
    if not session.open(hostname, port, username, password):
        sys.stderr.write("Error connecting to: " + hostname + ":" + str(telnet_port))
        sys.exit(-1)
    return session


def fix_patchid(patchid):
    """ Fix common errors in a patchid """
    patchid.replace(".", "-")
    elements = patchid.split("-")
    new_elements = []
    for element in elements:
        try:
            corrected_element = "%02d" % int(element)
        except ValueError:
            corrected_element = element
        new_elements.append(corrected_element)
    patchid_corrected = '-'.join(new_elements)
    return patchid_corrected


def get_available_patchports(hostname, port, username, password):
    """ Get all available patchports """
    global switchlist
    switchlist = CiscoSet(username, password, hostname, port)
    switchlist.discover_devices()
    all_ports = switchlist.execute_on_all(CiscoTelnetSession.get_interface_status_and_setting)
    all_ports_sorted = sorted(all_ports, key=lambda k: fix_patchid(k['patchid']))
    return all_ports_sorted


def get_health_status(hostname, port, username, password):
    global switchlist
    """ Get a list of the health status for each switch """
    if switchlist is None:
        switchlist = CiscoSet(username, password, hostname, port)
        switchlist.discover_devices()

    health_status = switchlist.execute_on_all(CiscoTelnetSession.show_health)
    return health_status


def get_available_vlans(hostname, port, username, password):
    """ Get all available VLANs """
    dynamic_vlan = {'vlanname': 'dynamic', 'vlanid': 'dynamic', 'status': 'software-generated'}
    trunk_vlan = {'vlanname': 'trunk', 'vlanid': 'trunk', 'status': 'software-generated'}
    try:
        session = connect_to_switch(hostname, port, username, password)
        vlans = session.show_vlan()
        vlans.append(dynamic_vlan)
        vlans.append(trunk_vlan)
        return vlans
    except BaseException:  # pylint: disable=bare-except
        return None


def get_available_vlannames(hostname, port, username, password):
    """ Extract all VLAN names """
    vlans = get_available_vlans(hostname, port, username, password)
    vlannames = [{'vlanname': x['vlanname'], 'vlanid': x['vlanid']} for x in vlans]
    return vlannames


def vlanname_to_vlanid(switch_hostname, port, username, password, vlanname):
    """ Convert a VLAN name to a VLAN id """
    vlans = get_available_vlans(switch_hostname, port, username, password)
    for vlan in vlans:
        cur_vlanid = vlan["vlanid"]
        cur_vlanname = vlan["vlanname"]
        if vlanname == cur_vlanname:
            return cur_vlanid
    return None


def get_port_from_patchid(hostname, port, username, password, patchid):
    """ Translate a patchid to a switchport """
    patches = get_available_patchports(hostname, port, username, password)
    for row in patches:
        if fix_patchid(row["patchid"]) == fix_patchid(patchid):
            return row
    return None


def configure_patchid_raw(username, password, switch_hostname, switchport, vlanid, old_vlanid):  # pylint: disable=too-many-arguments
    """ Perform the raw actions needed to configure a patchid """
    print "Going to set switchport %s of switch %s to vlanid %s (previously %s)..." % (switchport, switch_hostname, vlanid, old_vlanid)
    print "...Connecting to switch"
    session = connect_to_switch(switch_hostname, telnet_port, username, password)
    print "...Setting switchport..."
    if vlanid != "trunk":
        print '"' + session.set_interface_vlan(switchport, vlanid) + '"'
    else:
        print session.set_interface_trunk(switchport)
    print "...Saving configuration to nvram"
    session.save_config()
    print "Done"


def configure_patchid(username, password, patchid, vlanname):
    """ Configure a patchid """
    port = get_port_from_patchid(default_switch, telnet_port, username, password, patchid)
    vlanid = vlanname_to_vlanid(default_switch, telnet_port, username, password, vlanname)
    switch_hostname = port["hostname"]
    switchport = port["interface"]
    old_vlanid = port["vlanid"]
    configure_patchid_raw(username, password, switch_hostname, switchport, vlanid, old_vlanid)


if __name__ == '__main__':
    # This block initializes some variables depending on how we were called
    if len(sys.argv) < 3:
        sys.stderr.write(
            "Usage: " +
            sys.argv[0] +
            " first-switch username password    		to list all available patchports\n")
        sys.stderr.write(
            "Usage: " +
            sys.argv[0] +
            " first-switch username password patchnumber 	to list all available vlans\n")
        sys.stderr.write(
            "Usage: " +
            sys.argv[0] +
            " first-switch username password patchnumber vlan	to change the configuration of a port\n")
        sys.exit(-1)

    try:
        default_switch = str(sys.argv[1])
        main_username = str(sys.argv[2])
        main_password = str(sys.argv[3])
        main_patchnumber = str(sys.argv[4])
        main_vlanname = str(sys.argv[5])
    except IndexError:
        pass

    # This block determines how we run:
    if main_username is not None and \
            main_password is not None and \
            main_patchnumber is None and \
            main_vlanname is None:
        print_list(get_available_patchports(default_switch,
                                            telnet_port, main_username, main_password))
    elif main_username is not None and \
            main_password is not None and \
            main_patchnumber is not None and \
            main_vlanname is None:
        print_list(get_available_vlannames(default_switch,
                                           telnet_port, main_username, main_password))
    elif main_username is not None and \
            main_password is not None and \
            main_patchnumber is not None and \
            main_vlanname is not None:
        configure_patchid(main_username, main_password, main_patchnumber, main_vlanname)
    else:
        sys.stderr.write("AIEEE! This should never happen!\n")

    sys.exit(0)
