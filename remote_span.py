#!/usr/bin/env python
"""This file is the main routine for finding IPs in a Cisco-based network"""
import sys
import json

from Cisco import CiscoTelnetSession, CiscoSet
from portconfig import print_list

telnet_port = 23

def print_switchports(hostname, port, username, password):
	switch = CiscoTelnetSession()
	switch.open(hostname, port, username, password)
	ports = switch.show_interface_vlan()
	print_list(ports)	

def configure_remote_span(src_switch, src_port, src_interface, dst_switch, dst_port, dst_interface, span_vlan, username, password):
	span_session_number = (int(span_vlan) % 10) + 1 #map vlan number to a session number 1-10
	switchset = CiscoSet(username, password, src_switch, src_port)

	print "Discovering network"
	switchset.discover_devices()

	print "Removing all references to Remote SPAN session %d on vlan %d" % (span_session_number, span_vlan)
	switchset.execute_on_all(CiscoTelnetSession.clear_remote_span, span_session_number)

	print "Setting source switch " + src_switch
	source = CiscoTelnetSession()
	source.open(src_switch, src_port, username, password)
	source.remote_span(span_session_number, "interface " + src_interface, "remote vlan " + str(span_vlan))

	print "Setting destination switch " + dst_switch
	dest = CiscoTelnetSession()
	dest.open(dst_switch, dst_port, username, password)
	dest.remote_span(span_session_number, "remote vlan " + str(span_vlan), "interface " + dst_interface)

	print "Done"


if __name__ == '__main__':
	#This block initializes some variables depending on how we were called
	if len(sys.argv) < 5:
		sys.stderr.write("Usage: " + sys.argv[0] + " username password span-vlan-nr source-switch source-port destination-switch destination-port\n")
		sys.stderr.write("Usage: " + sys.argv[0] + " username password span-vlan-nr source-switch\n")
		sys.stderr.write("Usage: " + sys.argv[0] + " username password span-vlan-nr source-switch source-port destination-switch\n")
		sys.exit(-1)

	username	= str(sys.argv[1])
	password	= str(sys.argv[2])
	span_vlan	= None
	src_switch	= None
	src_port 	= None
	dst_switch	= None
	dst_port	= None
	port = 23
	try:	
		span_vlan	= int(sys.argv[3])
		src_switch 	= str(sys.argv[4])
		src_port 	= str(sys.argv[5])
		dst_switch 	= str(sys.argv[6])
		dst_port	= str(sys.argv[7])
	except IndexError:
		pass
	if	span_vlan is None and \
		src_switch is not None and \
		src_port is None and \
		dst_switch is None and \
		dst_port is None:
		print "Please enter a valid SPAN VLAN number. Use portconfig.py for details"
	elif	span_vlan is not None and \
		src_switch is not None and \
		src_port is None and \
		dst_switch is None and \
		dst_port is None:
		print_switchports(src_switch, port, username, password)
	elif	span_vlan is not None and \
		src_switch is not None and \
		src_port is not None and \
		dst_switch is not None and \
		dst_port is None:
		print_switchports(dst_switch, port, username, password)
	elif	span_vlan is not None and \
		src_switch is not None and \
		src_port is not None and \
		dst_switch is not None and \
		dst_port is not None:
		configure_remote_span(src_switch, port, src_port, dst_switch, port, dst_port, span_vlan, username, password)
	else:
		sys.stderr.write("AIEEE! This should never happen!")


	sys.exit(0)
