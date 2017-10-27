# nettools
Networking tools to handle networks of Cisco IOS-based switches. Written in Python.

## What it is used for.
The software is mostly used for configuring ports to specific VLANs. The patch-id of the port should follow a certain format and be present in the port's description field, in order to be picked up by nettools.
This format should match the regular expression `(?P<patchid>[a-z0-9_]+(\-|\.)[a-z0-9]+(\-|\.)[0-9]+[a-z]?)`
The software can also be used for:
* Adding/removing users on all equipment.
* Changing parameters on all switches.
* Finding equipment in your network, by collecting MAC tables and ARP tables.
* Blocking equipment in your network.
* Autoconfiguring equipment in your network.

## How it works.
The software is designed to use the Cisco Discovery Protocol to "discover" the network structure. The software uses the following procedure for this:
1. Connect to the first switch using telnet. Use the supplied username and password.
2. Collect all neighbors with the `show cdp neighbors` command.
3. Recursively connect to all neighbors and perform the same procedure.

This is performed in a parallel fashion, since Cisco IOS switches are usually pretty slow.

For the procedure to work, a number of conditions must be met:
* All switches must be registered in DNS with their hostname. For example, a switch called "switch01" must be registered as "switch01.example.com" in DNS.
* All switches must have CDP turned on. One could, theoretically, use LLDP instead of CDP btw.
* The user supplied to nettools must be registered on the switch with enough privileges.

## How to run this application
<<<<<<< HEAD
The application needs to be started with the following command:
* python NewGui.pyw _username password first-switch_

-or-
* python PortConfigGui.py _username password first-switch_

Keep in mind, there are several seperate functionalities / tools not implemented into the GUI

For instance:
* python remote_span _username password first-switch_ list
* python network_overview.py _username password router first-switch_
* python network_graph.py _username password first-switch_ > graph.dot && dot -Tsvg -Kdot -o graph.svg graph.dot


=======
The application is started as follows:
* python NewGui.pyw

It will then ask you for a username, password and a first switch to 
contact.
>>>>>>> refs/remotes/origin/master
