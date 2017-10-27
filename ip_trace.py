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
    # This block initializes some variables depending on how we were called
    if len(sys.argv) < 6:
        sys.stderr.write("Usage: " + sys.argv[0] +
                         " username password the-missing-IP router switch\n")
        sys.exit(-1)

    username = str(sys.argv[1])
    password = str(sys.argv[2])
    ip = str(sys.argv[3])
    router_hostname = str(sys.argv[4])
    switch_hostname = str(sys.argv[5])
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
    all_ports = switchset.execute_on_all(CiscoTelnetSession.show_interface_vlan)

    ip_mac = "0000.0000.0000"
    for arp_entry in arp:
        arp_entry_ip = arp_entry["ip"]
        arp_entry_mac = arp_entry["macaddress"]
        if arp_entry_ip == ip:
            ip_mac = arp_entry_mac

    results = []
    for mac_entry in mac:
        if mac_entry["macaddress"] == ip_mac:
            mac_entry.pop("macaddress_type")  # Remove uninteresting info before printing
            mac_entry["uncertainty"] = count_mac_addresses(
                mac, mac_entry["hostname"], mac_entry["port"])
            mac_entry["vlanname"] = get_vlan_name(vlans, mac_entry["vlanid"])
            mac_entry["patchid"] = get_port_patchid(
                all_ports, mac_entry["hostname"], mac_entry["port"])
            results.append(mac_entry)

    sorted_results = sorted(results, key=lambda k: k['uncertainty'])
    json_result = json.dumps(sorted_results)
    print json_result
