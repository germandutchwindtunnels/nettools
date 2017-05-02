#!/usr/bin/env python
"""This file is the main routine for finding IPs in a Cisco-based network"""
import sys
import json


from Cisco import CiscoTelnetSession, CiscoSet

telnet_port = 23

def get_vlan_name(vlan_list, vlan_id):
	"""Look up the vlan name by the vlan id, in a list returned by the switch"""
	for vlan in vlan_list:
		if vlan["vlanid"] == str(vlan_id):
			return vlan["vlanname"]

def count_mac_addresses(mac_addresses, switch_hostname, switch_port):
	"""Count the number of mac addresses seen on a single port"""
	count = 0
	for cur_mac_entry in mac_addresses:
		if cur_mac_entry["hostname"] == switch_hostname and cur_mac_entry["port"] == switch_port:
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

	vlan_switch = CiscoTelnetSession()
	vlan_switch.open(hostname, port, username, password)
	vlans = vlan_switch.show_vlan()

	arp = switchset.execute_on_all(CiscoTelnetSession.show_arp)
	mac = switchset.execute_on_all(CiscoTelnetSession.show_mac_address_table)

	ip_mac = "0000.0000.0000"
	for arp_entry in arp:
		arp_entry_ip  = arp_entry["ip"]
		arp_entry_mac = arp_entry["macaddress"]
		if arp_entry_ip == ip:
			ip_mac = arp_entry_mac

	results = []
	for mac_entry in mac:
		if mac_entry["macaddress"] == ip_mac:
			mac_entry.pop("macaddress_type") #Remove uninteresting info before printing
			mac_entry["uncertainty"] = count_mac_addresses(mac, mac_entry["hostname"], mac_entry["port"])
			mac_entry["vlanname"] = get_vlan_name(vlans, mac_entry["vlanid"])
			results.append(mac_entry)

	sorted_results = sorted(results, key=lambda k: k['uncertainty'])
	json_result = json.dumps(sorted_results)
	print json_result 
