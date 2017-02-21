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

"""This is the module defining the CiscoTelnetSession class"""
from telnetlib import Telnet
from sets import Set
import multiprocessing
import re
import time
import json
import sys
import socket

class CiscoTelnetSession(object):
	"""This class provides the interface to a Cisco router/switch over Telnet"""

	regex_protocol = '(?P<protocol>Internet)'
	regex_ip = '(?P<ip>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})'
	regex_age = '(?P<age>[0-9\-]+)'
	regex_arptype = '(?P<arptype>ARPA)'
	regex_vlanid = '(?P<vlanid>([0-9]+|unassigned|trunk))'
	regex_vlanname = '(?P<vlanname>[a-zA-Z][0-9a-zA-Z-_]*)'
	regex_vlanstatus = '(?P<vlanstatus>[a-z/]+)'
	regex_ports = '(?P<ports>[a-zA-Z0-9, /]*)'
	regex_macaddress = '(?P<macaddress>[0-9a-f\.]+)'
	regex_macaddress_type = '(?P<macaddress_type>(STATIC|DYNAMIC))'
	regex_port = '(?P<port>[a-zA-Z0-9/]+)'
	regex_whitespace = '\s+'
	regex_optionalwhitespace = '\s*'
	regex_deviceid = '(?P<deviceid>[.0-9A-Za-z-]+)'
	regex_lldp_deviceid = '(?P<deviceid>[.0-9A-Za-z-]{1,20})'
	regex_interface = '(?P<interface>(Gi|Fa|Te)[a-zA-Z]*\s*[0-9]/[0-9](/[0-9]{1,2})?)'
	regex_portid = regex_interface.replace("interface", "portid")
	regex_holdtime = '(?P<holdtime>[0-9]+)'
	regex_capabilities = '(?P<capabilities>([RTBSHIrP],?\s?)+)'
	regex_platform = '(?P<platform>[0-9a-zA-Z-]+)'
	regex_string = "[0-9a-zA-Z]+"
	regex_patchid = '(?P<patchid>[a-z0-9_]+(\-|\.)[a-z0-9]+(\-|\.)[0-9]+[a-z]?)'

	newline = "\n"
	character_time_spacing_seconds = 0.1
	line_time_spacing_seconds = 0.1

	def __init__(self):
		#Info for connecting and telnet
		self.host = ""
		self.port = 0
		self.username = ""
		self.password = ""
		self.session = 0
		self.prompt = "#"
		self.response_timeout = 10

	def __del__(self):
		#self.session.write("exit\n")
		self.session.close()

	def write_command(self, commandstr):
		"""Write a command to the peer"""
#		self.session.write(commandstr)
		commandstr_len = len(commandstr)
		for i in range(0, commandstr_len):
			self.session.write(commandstr[i])
			time.sleep(self.character_time_spacing_seconds)
			if commandstr[i] == '\n':
				time.sleep(self.line_time_spacing_seconds)

	def execute_command_lowlevel(self, command, timeout = None):
		"""Execute a command and return the result"""
		#print self.host + ".execute_command: " + command
		if timeout == None:
			timeout = self.response_timeout
		commandstr = command + self.newline #.strip() + self.newline

		self.write_command(commandstr)
		output = self.session.read_until(self.prompt, timeout)
		ret = output[:-len(self.prompt)]
		#print "%s: '%s'" % (command, ret)
		return ret

	def execute_command(self, command, timeout = None):
		"""Execute a command on the Cisco switch"""
		retries_remaining = 3
		while retries_remaining > 0:
			try:
				return self.execute_command_lowlevel(command, timeout)
			except EOFError:
				retries_remaining = retries_remaining - 1
				print "Got EOFError, reconnecting..."
				self.connect_and_login()

	def connect_and_login(self):
		"""Establish a Telnet connection and perform a login"""
		self.session = Telnet()
		try:
			self.session.open(self.host, self.port, self.response_timeout)
		except socket.timeout:
			return False

		if not self.login(self.username, self.password):
			return False

		try:
			self.execute_command_lowlevel("terminal length 0")
			self.execute_command_lowlevel("terminal width 0")
		except EOFError:
			return False

		return True

	def login(self, username, password):
		"""Log in at the Cisco machine"""
		output = self.session.read_until(":", self.response_timeout)
		if output.find("Username:") != -1:
			self.session.write(username + self.newline)
			self.session.read_until("Password:", self.response_timeout)
			self.session.write(password + self.newline)
			pass_response = self.session.read_until(self.prompt, self.response_timeout)
			if self.prompt not in pass_response:
				return False
		else:
			self.session.close()
			return False
		return True

	def open(self, host, port, username, password):
		""""Open a connection to a Cisco router/switch"""
		self.host = str(host) #In case we receive a Unicode string
		self.port = port
		self.prompt = self.host[:self.host.find(".")] + "#"
		self.username = username
		self.password = password
		connect_login_result = self.connect_and_login()
		return connect_login_result

	def close(self):
		""""Close the connection to the Cisco router/switch"""
		self.execute_command("exit")

#	def split_output(self, output):
#		splitted = output.split('\r\n')
#		return splitted

	def filter_output(self, output, regex):
		"""Filter output from a command"""
		result = {}
		result_list = []
		if isinstance(output, str):
			lines = [output]
		else:
			lines = output

		for line in lines:
			iterator = re.finditer(regex, line)
			try:
				while True:
					cur = iterator.next()
					result = cur.groupdict()
					result['hostname'] = self.host
					result_list.append(result)
			except StopIteration:
				pass

		return result_list


	def command_filter(self, command, regex, timeout = None):
		"""Execute a command and regex filter the output"""
		output = self.execute_command(command, timeout)
		result_list = self.filter_output(output, regex)
		return result_list

	def show_mac_address_table(self):
		""""Get a list of mac addresses known to the device, with associated port, type and vlanid"""
		command = "show mac address-table"
		regex = CiscoTelnetSession.regex_whitespace + CiscoTelnetSession.regex_vlanid + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_macaddress + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_macaddress_type + CiscoTelnetSession.regex_whitespace + CiscoTelnetSession.regex_port
		return self.command_filter(command, regex)

	def show_vlan(self):
		"""Return a list of VLANs,status and assigned ports"""
		command = "show vlan brief"
		regex = CiscoTelnetSession.regex_vlanid + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_vlanname + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_vlanstatus + CiscoTelnetSession.regex_whitespace
#		regex += CiscoTelnetSession.regex_ports
		return self.command_filter(command, regex)

	def show_neighbors(self):
		"""Return a list of Cisco Discovery Protocol neighbors"""
		command = "show cdp neighbors"
		regex = CiscoTelnetSession.regex_deviceid + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_interface + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_holdtime + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_capabilities + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_platform + CiscoTelnetSession.regex_optionalwhitespace
		regex += CiscoTelnetSession.regex_portid
		ret = self.command_filter(command, regex)
		return ret

	def show_interface_vlan(self):
		"""Return a list of ports and their VLAN assignment"""
		command = "show interface status"
		regex = CiscoTelnetSession.regex_interface + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_patchid + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_string + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_vlanid
		return self.command_filter(command, regex)

	def show_arp(self):
		"""Request the ARP table of the switch"""
		command = "show arp"
		regex = CiscoTelnetSession.regex_protocol + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_ip + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_age + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_macaddress + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_arptype + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_vlanname
		return self.command_filter(command, regex)

	def upload_file_tftp(self, src_filename, host, dest_filename):
		'''Upload a file through tftp'''
		regex = '(?P<bytes>[0-9]+)\sbytes\s'
		command = "copy " + src_filename + " tftp://" + host + "/" + dest_filename + self.newline + self.newline #+ self.newline# + "#dummy suffix"
		command = command.replace("HOSTNAME", self.host)
#		print self.host + ": command='" + command + "'"
		output = self.command_filter(command, regex, 60)
		#output = self.execute_command(command, 60)
		#result_list = self.filter_output(output, regex)
		ret = "-1"
		#print self.host + ": output=\n'" + output + "'"
		if len(output) > 0:
			ret = output[0]['bytes']
		return ret

	def save_config(self):
		'''Copy running config to startup config'''
		return self.execute_command("copy run start" + self.newline)

	def add_user(self, username, password, privilege_level = 15):
		'''Add a user'''
		cmd = "config terminal" + self.newline + "no username " + str(username) + self.newline + "username " + str(username) + " privilege " + str(privilege_level) + " secret " + str(password) + self.newline + "end"
		ret = self.execute_command(cmd)
		return ret

	def enable_telnet_login(self):
		'''Force login on telnet'''
		cmd = "config terminal" + self.newline + "line vty 0 4" + self.newline + "login local" + self.newline + "end" + self.newline
		return self.execute_command(cmd)

	def show_lldp_neighbors(self):
		'''Show LLDP neighbors'''
		command = "show lldp neighbors"
		regex = CiscoTelnetSession.regex_lldp_deviceid + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_interface + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_holdtime + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_capabilities + CiscoTelnetSession.regex_whitespace
		regex += CiscoTelnetSession.regex_portid
		return self.command_filter(command, regex)

	def show_lldp_neighbor_detail(self, neighbor):
		'''Show details of an LLDP neighbor'''
		command = "show lldp neighbor " + neighbor + " detail"
		output = self.execute_command(command)
		splitted_output = output.split('\r\n')
		ret = {}
		for line in splitted_output:
			colon = ": "
			colonpos = line.find(colon)
			if colonpos == -1:
				continue
			key_end = colonpos
			value_start = colonpos + len(colon)
			key = line[:key_end].lstrip()
			value = line[value_start:].rstrip()
			ret[key] = value
		return ret

	def set_single_interface_description(self, interface, description):
		'''Produce the command to set the description of a single interface'''
		command = "interface " + interface + self.newline
		command += "description " + description	+ self.newline
		command += "exit" + self.newline
		return command

	def set_interface_description(self, interface, description):
		'''Set the description of an interface'''
		command = "config t" + self.newline
		command += self.set_single_interface_description(interface, description)
		command += "end" + self.newline
		output = self.execute_command(command)
		return output

	def set_interfaces_descriptions(self, interfaces_descriptions):
		'''Set the description of a list of interfaces'''
		command = "config t" + self.newline
		for interface in interfaces_descriptions.iterkeys():
			description = interfaces_descriptions[interface]
			command += self.set_single_interface_description(interface, description)
		command += "end" + self.newline
		output = self.execute_command(command)
		return output

	def set_single_interface_vlan(self, interface, vlanid):
		'''Produce the command to set the VLAN id for a singe interface'''
		command = "interface " + interface + self.newline
		command += "shutdown" + self.newline
		command += "switchport mode access" + self.newline
		command += "switchport access vlan " + vlanid + self.newline
		command += "no shutdown" + self.newline
		command += "exit" + self.newline
		return command

	def set_single_interface_voice_vlan(self, interface, voice_vlanid):
		'''Produce the command to set the Voice VLAN id for a single interface'''
		command = "interface " + interface + self.newline
		command += "shutdown" + self.newline
		command += "switchport mode access" + self.newline
		if voice_vlanid is None:
			command += "no switchport voice vlan" + self.newline
		else:
			command += "switchport voice vlan " + voice_vlanid + self.newline
		command += "no shutdown" + self.newline
		command += "exit" + self.newline
		return command

	def set_interface_vlan(self, interface, vlanid):
		'''Set the VLAN ID of an interface'''
		command = ""
		command += "config t" + self.newline
		command += self.set_single_interface_vlan(interface, vlanid)
		command += "end" + self.newline
		output = self.execute_command(command)
		return output

	def set_interface_vlan_voice_vlan(self, interface, vlanid, voice_vlanid):
		'''Set the VLAN ID and Voice VLAN ID of an interface'''
		command = ""
		command += "config t" + self.newline
		command += self.set_single_interface_vlan(interface, vlanid)
		command += self.set_single_interface_voice_vlan(interface, voice_vlanid)
		command += "end" + self.newline
		output = self.execute_command(command)
		return output

	def set_single_interface_trunk(self, interface):
		'''Produce the command to set a single interaface to mode trunk'''
		command = "interface " + interface + self.newline
		command += "shutdown" + self.newline
		command += "switchport trunk encap dot1q" + self.newline
		command += "switchport mode trunk" + self.newline
		command += "no shutdown" + self.newline
		command += "exit" + self.newline
		return command

	def set_interface_trunk(self, interface):
		"""Set the interface to 802.1q trunk mode"""
		command = ""
		command += "config t" + self.newline
		command += self.set_single_interface_trunk(interface)
		command += "end" + self.newline
		output = self.execute_command(command)
		return output

#	def merge_outputs(self, outputs):
#		output = []
#		for key,values in outputs.iteritems():
#			for value in values:
#				value['hostname'] = key
#				output.append(value)
#		return output

#	def deduplicate_output(self, items, unique_key, conflict_resolver):
#		output = []
#		for item in items:
#			key = item[unique_key]

#	def execute_on_neighbor(self, hostname, command, covered_neighbors, output, *args):
#		"""Connect to a neighbor and execute the specified command. Depricated"""
#		neighbor = CiscoTelnetSession()
#		neighbor_open_result = neighbor.open(hostname, self.port, self.username, self.password)
#		if neighbor_open_result:
#			neighbor._execute_on_all_neighbors(command, covered_neighbors, output, *args)
#		else:
#			sys.stderr.write(self.host + ".execute_on_neighbor: failed to connect to " + hostname + "\n")

#	def execute_on_all_neighbors(self, command, *args):
#		covered_neighbors = [ self.host ]
#		output = {}
#		ret = self.execute_on_neighbors_blacklist(command, covered_neighbors, *args)
#		return ret

#	def execute_on_neighbors_blacklist(self, command, blacklist, *args):
#		output = {}
#		ret = self._execute_on_all_neighbors(command, blacklist, output, *args)
#		return ret


#	def _execute_on_all_neighbors(self, command, covered_neighbors, output, *args):
#		printable_args = args
#		print "Executing command '%s' on switch %s %s" % (command, str(self.host), str(printable_args))
#		output[self.host] = command(self, *args)
#		#print "Output: %s" % output[self.host]
#
#		neighbors = self.show_neighbors()
		#print neighbors
#		for neighbor in neighbors:
#			self.execute_command("#keepalive")
#			neighbor_hostname = neighbor["deviceid"]
#			if neighbor_hostname not in covered_neighbors:#Make sure we don't run in cycles
#				covered_neighbors.append(neighbor_hostname)
#				self.execute_on_neighbor(neighbor_hostname, command, covered_neighbors, output, *args)
#
#		return output


class CiscoSet(object):
	"""This class represents a set of Cisco switches, connected in a network"""

	def __init__(self, username, password, start_device, port):
		self.username = username
		self.password = password
		self.start_device = start_device
		self.port = port
		self.seen = [ start_device ]
		self.blacklist = []

	def get_serialize_filename(self):
		"""Get the filename to serialize this set to"""
		filename = "discover-%s.json" % self.start_device
		return filename

	def load(self):
		"""Load from file"""
		filename = self.get_serialize_filename()
		seen = self.seen
		try:
			fd = open(filename, "r")
			json_contents = fd.read()
			json_decoded = json.loads(json_contents)
			self.seen = json_decoded
		except IOError:
			pass #Doesn't matter, we'll create it on save
		except ValueError:
			self.seen = seen #Restore backup of seen when we encounter problems during decoding

	def save(self):
		"""Save to file"""
		filename = self.get_serialize_filename()
		fd = open(filename, "w+")
		json_contents = json.dumps(self.seen)
		fd.write(json_contents)



	def set_blacklist(self, blacklist):
		"""Don't connect to these hosts"""
		self.blacklist = blacklist

#	def _crawl_neighbors(self, device):
#		"""Get all neighbors from a device"""
#		neighbors = device.show_neighbors()
#		neighbors_hostnames = [ neighbor["deviceid"] for neighbor in neighbors ]
#		for neighbor_hostname in neighbors_hostnames:
#			if neighbor_hostname not in self.seen:
#				self.discover_devices()

	def discover_devices(self):
		'''Discover all networking devices, using a depth-first search.'''
		self.load() #Attempt to bootstrap using a saved json file
		last_count = 0
		while last_count != len(self.seen):
			last_count = len(self.seen)
			outputs = self.execute_on_all(CiscoTelnetSession.show_neighbors)
			neighborslist = [ x for x in outputs ] #Concatenate all outputs to one
			neighbor_hostnames = [ x['deviceid'] for x in neighborslist ]
			all_devices = self.seen + neighbor_hostnames
			all_devices_uniq = uniq(all_devices)
			self.seen = all_devices_uniq
			print "Seen: " + str(self.seen)
		self.save() #Save what we've found for the next time

	def execute_on_all(self, command, *args):
		"""Execute command on all devices"""
		cpu_count = 50 #multiprocessing.cpu_count()
		command_name = command.__name__
		print "Process count %d" % cpu_count
		pool = multiprocessing.Pool(processes=cpu_count)

		results = [ pool.apply_async(execute_on_device, (host, self.port, self.username, self.password, command_name) + args) for host in self.seen if host not in self.blacklist ]
		ret = [ ]
		for res in results:
			try:
				ret = ret + res.get()
			except TypeError:
				ret = ret + [res.get()]
		return ret

def uniq(seq):
	"""Remove duplicates from list"""
	s = Set(seq)
	unique = list(s)
	unique_sorted = sorted(unique)
	return unique_sorted

def execute_on_device(hostname, port, username, password, command_name, *args):
	"""Helper function for CiscoSet.discover_devices"""
	device = CiscoTelnetSession()
	open_result = device.open(hostname, port, username, password)
#	object_functions = dir(device)
	command = getattr(device, command_name, None)
	if command is None:
		sys.stderr.write("execute_on_device: failed to look up function %s in CiscoTelnetSession class\n" % command_name)
		return None

	ret = []
	if open_result:
		ret = command(*args)
	else:
		sys.stderr.write("execute_on_device: failed to connect to " + hostname + "\n")
	return ret
