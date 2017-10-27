#!/usr/bin/env python
""" This file is the main routine for finding IPs in a Cisco-based network """
import sys
import json

from Cisco import CiscoTelnetSession, CiscoSet
from portconfig import print_list

telnet_port = 23


def print_switchports(hostname, portnr, user, pwd):
    """ Print all switchports with a good description on a given switch """
    switch = CiscoTelnetSession()
    switch.open(hostname, portnr, user, pwd)
    ports = switch.show_interface_vlan()
    print_list(ports)



def span_session_from_vlan(spanvlan):
    """ Translate a SPAN vlan number to a session number """
    span_session_number = (int(spanvlan) % 10) + 1  # map vlan number to a session number 1-10
    return span_session_number



def erase_remote_span_session(switchset, span_session_number):
    """ Erase a remote span session on a previously established CiscoSet """
    switchset.execute_on_all(CiscoTelnetSession.clear_remote_span, span_session_number)



def discover_erase_span(user, pwd, switch, spansession):
	"""Discover the network from switch and remote a span session"""
	span_session_number = int(spansession)
	switchset = CiscoSet(user, pwd, switch, telnet_port)
	switchset.discover_devices()
	erase_remote_span_session(switchset, span_session_number)
	output = switchset.execute_on_all(CiscoTelnetSession.show_span)
	json_output = json.dumps(output)
	print json_output


def list_span_sessions(user, pwd, switch):
    """ Show all current span sessions """
    switchset = CiscoSet(user, pwd, switch, telnet_port)
    switchset.discover_devices()
    output = switchset.execute_on_all(CiscoTelnetSession.show_span)
    json_output = json.dumps(output)
    print json_output



def configure_remote_span(srcswitch, srcport, srcinterface, dstswitch, dstinterface, spanvlan, user, pwd): #pylint: disable=too-many-arguments
	"""Configure a remote span session on both switches"""
	dstport = srcport
	switchset = CiscoSet(user, pwd, srcswitch, srcport)
	span_session_number = spanvlan

	#print "Discovering network"
	switchset.discover_devices()

	#print "Removing all references to Remote SPAN session %d on vlan %d" % (span_session_number, span_vlan)
	erase_remote_span_session(switchset, span_session_number)
	if srcswitch == dstswitch: # No Remote needed on the same switch.
		source = CiscoTelnetSession()
		source.open(srcswitch, srcport, user, pwd)
		source.remote_span(span_session_number, "interface " + srcinterface, "interface " + dstinterface)
	else:
		#print "Setting source switch " + srcswitch
		source = CiscoTelnetSession()
		source.open(srcswitch, srcport, user, pwd)
		source.remote_span(span_session_number, "interface " + srcinterface, "remote vlan " + str(spanvlan))

		#print "Setting destination switch " + dstswitch
		dest = CiscoTelnetSession()
		dest.open(dstswitch, dstport, user, pwd)
		dest.remote_span(span_session_number, "remote vlan " + str(spanvlan), "interface " + dstinterface)

	output = switchset.execute_on_all(CiscoTelnetSession.show_span)
	json_output = json.dumps(output)
	print json_output


if __name__ == '__main__':
	#This block initializes some variables depending on how we were called
	if len(sys.argv) < 5:
		sys.stderr.write("Usage: " + sys.argv[0] + " username password source-switch clear session-nr\n")
		sys.stderr.write("Usage: " + sys.argv[0] + " username password source-switch list\n")
		sys.stderr.write("Usage: " + sys.argv[0] + " username password source-switch source-port destination-switch destination-port session-nr\n")
		sys.stderr.write("Usage: " + sys.argv[0] + " username password source-switch source-port destination-switch destination-port\n")
		sys.stderr.write("Usage: " + sys.argv[0] + " username password source-switch source-port destination-switch\n")
		sys.stderr.write("Usage: " + sys.argv[0] + " username password source-switch source-port\n")
		sys.stderr.write("Usage: " + sys.argv[0] + " username password source-switch\n")
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
		src_switch 	= str(sys.argv[3])
		src_port 	= str(sys.argv[4])
		dst_switch 	= str(sys.argv[5])
		dst_port	= str(sys.argv[6])
		span_vlan	= int(sys.argv[7])
	except IndexError:
		pass
	if	src_switch is not None and \
		src_port == "list":
		list_span_sessions(username, password, src_switch)
	elif	src_switch is not None and \
		src_port == "clear" and \
		dst_switch is not None:
		discover_erase_span(username, password, src_switch, dst_switch) #dst_switch is now span-vlan-nr
	elif	span_vlan is None and \
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
		configure_remote_span(src_switch, port, src_port, dst_switch, dst_port, span_vlan, username, password)
	else:
		sys.stderr.write("AIEEE! This should never happen!")


	sys.exit(0)
