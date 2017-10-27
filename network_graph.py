#!/usr/bin/env python
""" This file is the main routine for finding IPs in a Cisco-based network """
import sys

from Cisco import CiscoTelnetSession, CiscoSet

telnet_port = 23

if __name__ == '__main__':
    # This block initializes some variables depending on how we were called
    if len(sys.argv) < 4:
        sys.stderr.write("Usage: " + sys.argv[0] + " username password switch > graph.dot\n")
        sys.stderr.write("dot -Tsvg -Kdot -o graph.svg graph.dot\n")
        sys.exit(-1)

    username = str(sys.argv[1])
    password = str(sys.argv[2])
    switch_hostname = str(sys.argv[3])
    port = 23

    switchset = CiscoSet(username, password, switch_hostname, port)
    switchset.discover_devices()

    neighbors = switchset.execute_on_all(CiscoTelnetSession.show_neighbors)

    print "digraph \"" + switch_hostname + "\" {"
    for neighbor in neighbors:
        print "\"" + neighbor["hostname"] + "\" -> \"" + neighbor["deviceid"] + "\";"
    print "}"
