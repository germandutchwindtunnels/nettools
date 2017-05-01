#!/usr/bin/env python
import sys

#import SVN
#import Patchlist 
from Cisco import CiscoTelnetSession, CiscoSet

telnet_port = 23

def print_list(thelist):
	thelist_str = [ str(x) for x in thelist ]
	output = '\n'.join(thelist_str)
	print output

if __name__ == '__main__':
	#This block initializes some variables depending on how we were called
	if len(sys.argv) < 4:
		sys.stderr.write("Usage: " + sys.argv[0] + " username password hostname\n")
		sys.exit(-1)
	
	username = str(sys.argv[1])
	password = str(sys.argv[2])
	hostname = str(sys.argv[3])
	port = 23

	switchset = CiscoSet(username, password, hostname, port)
	switchset.discover_devices()
	
	
	print_list(switchset.execute_on_all(CiscoTelnetSession.show_arp))
	print_list(switchset.execute_on_all(CiscoTelnetSession.show_mac_address_table))
	


		
