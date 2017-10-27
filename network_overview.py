#!/usr/bin/env python
""" This file is the main routine for finding IPs in a Cisco-based network """
import sys
import json

from Cisco import CiscoTelnetSession, CiscoSet

telnet_port = 23


def get_port_patchid(port_list, hostname_switch, switch_port):
    """ Look up the patchid of a port """
    for cur_port in port_list:
        if cur_port["interface"] == switch_port and cur_port["hostname"] == hostname_switch:
            return cur_port["patchid"]
    return None


def get_vlan_name(vlan_list, vlan_id):
    """ Look up the vlan name by the vlan id, in a list returned by the switch """
    for vlan in vlan_list:
        if vlan["vlanid"] == str(vlan_id):
            return vlan["vlanname"]


def count_mac_addresses(mac_addresses, hostname, switch_port):
    """ Count the number of mac addresses seen on a single port """
    count = 0
    for cur_mac_entry in mac_addresses:
        if cur_mac_entry["hostname"] == hostname and cur_mac_entry["port"] == switch_port:
            count = count + 1
    return count


if __name__ == '__main__':
	#This block initializes some variables depending on how we were called
	if len(sys.argv) < 5:
		sys.stderr.write("Usage: " + sys.argv[0] + " username password router switch\n")
		sys.exit(-1)

	username	= str(sys.argv[1])
	password	= str(sys.argv[2])
	router_hostname	= str(sys.argv[3])
	switch_hostname	= str(sys.argv[4])
	port = 23



	router = CiscoTelnetSession()
	router.open(router_hostname, port, username, password)
	arp = router.show_arp()

	switchset = CiscoSet(username, password, switch_hostname, port)
	switchset.discover_devices()

	vlan_switch = CiscoTelnetSession()
	vlan_switch.open(switch_hostname, port, username, password)
	vlans = vlan_switch.show_vlan()

	mac = switchset.execute_on_all(CiscoTelnetSession.show_mac_address_table)
	all_ports = switchset.execute_on_all(CiscoTelnetSession.get_interface_status_and_setting)
	for port in all_ports:
		try:
			port["vlanname"] = get_vlan_name(vlans, port["vlanid"])
			port["vlanconfigname"] = get_vlan_name(vlans, port["vlanconfig"])
		except KeyError:
			pass

	port_settings = switchset.execute_on_all(CiscoTelnetSession.get_interface_vlan_setting)
	for port_setting in port_settings:
		port_setting["interface"] = CiscoTelnetSession.fix_interfacename(port_setting["interface"])

	for mac_entry in mac:
		mac_entry.pop("macaddress_type") #Remove uninteresting info before printing
		mac_entry["uncertainty"] = count_mac_addresses(mac, mac_entry["hostname"], mac_entry["port"])
		mac_entry["vlanname"] = get_vlan_name(vlans, mac_entry["vlanid"])
		mac_entry["patchid"] = get_port_patchid(all_ports, mac_entry["hostname"], mac_entry["port"])
	    
	rspan = switchset.execute_on_all(CiscoTelnetSession.show_span)

	neighbors = switchset.execute_on_all(CiscoTelnetSession.show_neighbors)

	json_list = { "arp" : arp, "mac" : mac, "ports" : all_ports, "vlans" : vlans, "rspan" : rspan, "neighbors" : neighbors}
	print json.dumps(json_list)
