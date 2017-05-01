#!/usr/bin/env python
import sys

#import SVN
#import Patchlist 
from Cisco import CiscoTelnetSession, CiscoSet

telnet_port = 23

#TODO: This could be optimized for repeated calls using a dict for caching... but who cares about performance, right?
def count_mac_addresses(mac_addresses, hostname, port):
	count = 0
	for mac_entry in mac_addresses:
		if mac_entry["hostname"] == hostname and mac_entry["port"] == port:
			count = count + 1
	return count

if __name__ == '__main__':
	#This block initializes some variables depending on how we were called
	if len(sys.argv) < 5:
		sys.stderr.write("Usage: " + sys.argv[0] + " username password first-switch-hostname the-missing-IP\n")
		sys.exit(-1)
	
	username = str(sys.argv[1])
	password = str(sys.argv[2])
	hostname = str(sys.argv[3])
	ip = str(sys.argv[4])
	port = 23

	switchset = CiscoSet(username, password, hostname, port)
	switchset.discover_devices()


	arp = switchset.execute_on_all(CiscoTelnetSession.show_arp)
	mac = switchset.execute_on_all(CiscoTelnetSession.show_mac_address_table)

	ip_mac = "0000.0000.0000"
	for arp_entry in arp:
		arp_entry_ip  = arp_entry["ip"]
		arp_entry_mac = arp_entry["macaddress"]
		if(arp_entry_ip == ip):
			ip_mac = arp_entry_mac

	for mac_entry in mac:
		if mac_entry["macaddress"] == ip_mac:
			mac_entry.pop("macaddress_type") #Remove uninteresting info before printing
			mac_entry["uncertainty"] = count_mac_addresses(mac, mac_entry["hostname"], mac_entry["port"])
			print mac_entry
	
		
