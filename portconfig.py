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

import sys
import socket

#import Patchlist 
from Cisco import CiscoTelnetSession
from Cisco import CiscoSet


my_fqdn = socket.getfqdn()
hostname = socket.gethostname()
dns_domain = my_fqdn[len(hostname):] 
telnet_port = 23

#Patchlist stuff
patchlist_patchid_column = "Patchnr"

#Init global vars
patchnumber = None
vlanname = None
username = None
password = None

def print_list(thelist):
	thelist_str = [ str(x) for x in thelist ]
	output = '\n'.join(thelist_str)
	print output

def connect_to_switch(hostname, port, username, password):
	session = CiscoTelnetSession()
	if not session.open(hostname, port, username, password):
	       sys.stderr.write("Error connecting to: " + hostname + ":" + str(telnet_port))
	       sys.exit(-1)
	return session

def fix_patchid(patchid):
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
	switches = CiscoSet(username, password, hostname, port)
	switches.discover_devices()
	all_ports = switches.execute_on_all(CiscoTelnetSession.show_interface_vlan)
	all_ports_sorted = sorted(all_ports, key=lambda k : fix_patchid(k['patchid']))
	return all_ports_sorted


def get_available_vlans(hostname, port, username, password):
	dynamic_vlan = { 'vlanname' : 'dynamic', 'vlanid' : 'dynamic', 'status' : 'software-generated' }
	trunk_vlan = { 'vlanname' : 'trunk', 'vlanid' : 'trunk', 'status' : 'software-generated' }
	try:
		session = connect_to_switch(hostname, port, username, password)
		vlans = session.show_vlan()
		vlans.append(dynamic_vlan)
		vlans.append(trunk_vlan)
		vlans_sorted = sorted(vlans, key=lambda k: k['vlanid'])
		return vlans
	except:
		return None

def get_available_vlannames(hostname, port, username, password):
	vlans = get_available_vlans(hostname, port, username, password)
	vlannames = [ { 'vlanname' : x['vlanname'], 'vlanid' : x['vlanid'] } for x in vlans ]
	vlannames_sorted = sorted(vlannames, key=lambda k : k['vlanid'])
	return vlannames

def vlanname_to_vlanid(switch_hostname, port, username, password, vlanname):
	vlans = get_available_vlans(switch_hostname, port, username, password)
	for vlan in vlans:
		cur_vlanid = vlan["vlanid"]
		cur_vlanname = vlan["vlanname"]
		if vlanname == cur_vlanname:
			return cur_vlanid
	return None

def get_port_from_patchid(hostname, port, username, password, patchid):
	patches = get_available_patchports(hostname, port, username, password)
	for row in patches:
		if fix_patchid(row["patchid"]) == fix_patchid(patchid):
			return row
	return None
	
def configure_patchid_raw(username, password, switch_hostname, switchport, vlanid, old_vlanid):
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
	port = get_port_from_patchid(default_switch, telnet_port, username, password, patchid)
	vlanid = vlanname_to_vlanid(default_switch, telnet_port, username, password, vlanname)
	switch_hostname = port["hostname"]
	switchport = port["interface"]
	old_vlanid = port["vlanid"]
	configure_patchid_raw(username, password, switch_hostname, switchport, vlanid, old_vlanid)
	
if __name__ == '__main__':
	#This block initializes some variables depending on how we were called
	if len(sys.argv) < 3:
		sys.stderr.write("Usage: " + sys.argv[0] + "first-switch username password    		to list all available patchports\n")
		sys.stderr.write("Usage: " + sys.argv[0] + "first-switch username password patchnumber 	to list all available vlans\n")
		sys.stderr.write("Usage: " + sys.argv[0] + "first-switch username password patchnumber vlan	to change the configuration of a port\n")
		sys.exit(-1)
	
	try:	
		default_switch = str(sys.argv[1])
		username = str(sys.argv[2])
		password = str(sys.argv[3])
		patchnumber = str(sys.argv[4])
		vlanname = str(sys.argv[5])
	except IndexError:
		pass


	
	#This block determines how we run:
	if 	username is not None and \
		password is not None and \
		patchnumber is None and \
		vlanname is None:
		print_list(get_available_patchports(default_switch, telnet_port, username, password))
	elif 	username is not None and \
		password is not None and \
		patchnumber is not None and \
		vlanname is None:
		print_list(get_available_vlannames(default_switch, telnet_port, username, password))
	elif	username is not None and \
		password is not None and \
		patchnumber is not None and \
		vlanname is not None:
		configure_patchid(username, password, patchnumber, vlanname)
	else:
		sys.stderr.write("AIEEE! This should never happen!\n")
	
	sys.exit(0)


	row = Network.search_patchlist(patchlist_filename, "Patchnr", patchnumber, Network.fix_patchid)
	
	#Determine which switch to connect to
	switch_hostname = row["Switch name"]
	switch_fqdn = switch_hostname + "." + dns_domain
	
	session = CiscoTelnetSession()
	if not session.open(switch_hostname, telnet_port, username, password):
		sys.stderr.write("Error connecting to: " + switch_hostname + ":" + str(telnet_port))
		sys.exit(-1)
	
	#Translate vlan name to vlan id
	vlans = session.show_vlan()
	print vlans
	
	portname = row["Interface"]
		
