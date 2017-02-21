#!/usr/bin/env python
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

''' A New GUI for nettools. '''

import sys, re
# import pprint

import portconfig

from PyQt4.QtGui import QApplication, QMessageBox, QTreeWidgetItem, QComboBox
from PyQt4.QtGui import QPushButton
from PyQt4.QtCore import QThread, pyqtSignal
import PyQt4.uic as uic

class WorkerThread(QThread):
    ''' Perform a background job. Emits a "finished" signal when done. '''

    def __init__(self, username, password):
        ''' Initialisation. '''

        QThread.__init__(self)

        self._user = username
        self._pass = password

class GetConfigurationThread(WorkerThread):
    ''' Get the network configuration in the background. Emits the "newData"
        signal with patchports and vlans when done, then emits the "finished"
        signal. '''

    newData = pyqtSignal(dict)

    def __init__(self, hostname, username, password):
        ''' Initialisation. '''

        WorkerThread.__init__(self, username, password)

        self._host = hostname

    def run(self):
        ''' Run this thread. '''

        data = {
            'ports': portconfig.get_available_patchports(self._host, 23,
                                                         self._user,
                                                         self._pass),
            'vlans': portconfig.get_available_vlans(self._host, 23,
                                                    self._user,
                                                    self._pass)
        }

        self.newData.emit(data)

class SetConfigurationThread(WorkerThread):
    ''' Set the network configuration in the background. Emits the "finished"
        signal when done. '''

    def __init__(self, username, password):
        WorkerThread.__init__(self, username, password)

        self._jobs = [ ]

    def addJob(self, switch_host, switch_port, old_vlan_id, new_vlan_id):
        ''' Add a job configuring <switch_port> on <switch_host> from
            <old_vlan_id> to <new_vlan_id>. '''

        self._jobs.append( {
            'switch_host': switch_host,
            'switch_port': switch_port,
            'old_vlan_id': old_vlan_id,
            'new_vlan_id': new_vlan_id
        } )

    def jobCount(self):
        ''' Return the number of jobs defined for this thread. '''

        return len(self._jobs)

    def run(self):
        ''' Run this thread. '''

        for job in self._jobs:
            portconfig.configure_patchid_raw(self._user, self._pass,
                                             job['switch_host'],
                                             job['switch_port'],
                                             job['new_vlan_id'],
                                             job['old_vlan_id'])

        self._jobs = [ ]

class MyComboBox(QComboBox):
    ''' A subclass of the PyQt4 QComboBox that ignores mouse wheel events. '''

    def wheelEvent(self, event):    # pylint: disable=no-self-use
        """ Pass through mouse wheel events, so they scroll the underlying table
            instead of this combo box. """

        event.ignore()

class NewGui(QApplication):
    ''' Port Configurator GUI. '''

    def __init__(self, args):
        ''' Initialisation. '''

        QApplication.__init__(self, args)

        self._ports = [ ]
        self._vlans = [ ]

        self._vlan_id_to_label = { }

        self._msg_box = None

        self._get_config_thread = None
        self._set_config_thread = None

        if len(args) == 4:
            self._user = args[1]
            self._pass = args[2]
            self._host = args[3]
        else:
            self._usage(-1)

        self._win = uic.loadUi("NewGui.ui")

        self._win.ports.itemExpanded.connect(lambda item: self._resize())
        self._win.ports.itemCollapsed.connect(lambda item: self._resize())

        self._win.buttonReload.pressed.connect(self._get_configuration)
        self._win.buttonSubmitAll.pressed.connect(self._submit_all)

        self._win.show()

        self._get_configuration()

    @staticmethod
    def _usage(exit_code):
        ''' Show usage and exit with <exit_code>. '''

        sys.stderr.write("Usage: " \
                         + sys.argv[0]\
                         + " <username> <password> <first-switch>\n")

        sys.exit(exit_code)

    def _handle_new_data(self, data):
        ''' Handle data from the GetConfigurationThread. '''

        self._ports = data['ports']
        self._vlans = data['vlans']

        self._vlan_id_to_label = { }

        for i, vlan in enumerate(self._vlans):
            vlan['label'] = '%s (%s)' % (vlan['vlanid'], vlan['vlanname'])

            self._vlan_id_to_label[vlan['vlanid']] = i

        for i, port in enumerate(self._ports):
            if port['vlanid'] == 'unassigned':
                self._ports[i]['vlanid'] = 'dynamic'

        # print "Ports:"
        # pprint.pprint(self._ports)

        # print "VLANs:"
        # pprint.pprint(self._vlans)

        self._refresh()

    def _get_config_thread_finished(self):
        ''' Handle completion of the GetConfigurationThread. '''

        self._get_config_thread.deleteLater()

        if self._msg_box:
            self._msg_box.hide()
            self._msg_box.deleteLater()
            self._msg_box = None

    def _show_message(self, text):
        ''' Show an informational message box with <text>. '''

        self._msg_box = QMessageBox(self._win)

        self._msg_box.setIcon(QMessageBox.Information)
        self._msg_box.setWindowTitle("Working...")
        self._msg_box.setText(text)

        self._msg_box.setStandardButtons(QMessageBox.NoButton)

        self._msg_box.show()

    def _get_configuration(self):
        ''' Get the current network configuration. '''

        self._win.ports.clear()

        self._show_message('Getting switch configuration; please wait.')

        self._get_config_thread = GetConfigurationThread(self._host,
                                                         self._user,
                                                         self._pass)
        self._get_config_thread.newData.connect(
            self._handle_new_data)
        self._get_config_thread.finished.connect(
            self._get_config_thread_finished)
        self._get_config_thread.start()

    def _resize(self):
        ''' Resize the columns of the data table based on its current contents.
        '''

        for col in range(self._win.ports.columnCount()):
            self._win.ports.resizeColumnToContents(col)

    def _refresh(self):
        ''' Refresh the data table based on the current data. '''

        self._win.ports.clear()

        for index, port in enumerate(self._ports):
            self._ports[index]['item'] = self._add_to_tree(port)

        self._resize()

    def _set_config_thread_finished(self):
        ''' Handle completion of the SetConfigurationThread. '''

        self._set_config_thread.deleteLater()

        if self._msg_box:
            self._msg_box.hide()
            self._msg_box.deleteLater()
            self._msg_box = None

    def _submit_pressed(self, port, item):
        ''' The user has pressed the Submit button for <port> in QTreeWidgetItem
            <item>. Handle this.'''

        current_index = self._win.ports.itemWidget(item, 3).currentIndex()

        switch_host = port['hostname']
        switch_port = port['interface']
        old_vlan_id = port['vlanid']
        new_vlan_id = self._vlans[current_index - 1]['vlanid']

        self._show_message('Setting port %s to vlan %s; please wait.' %
                           (port['patchid'], new_vlan_id))

        self._set_config_thread = SetConfigurationThread(self._user, self._pass)
        self._set_config_thread.addJob(switch_host, switch_port,
                                       old_vlan_id, new_vlan_id)
        self._set_config_thread.finished.connect(
            self._set_config_thread_finished)
        self._set_config_thread.start()

    def _submit_all(self):
        ''' The user has pressed the "Submit all" button. Handle this. '''

        self._set_config_thread = SetConfigurationThread(self._user, self._pass)
        self._set_config_thread.finished.connect(
            self._set_config_thread_finished)

        text = ""

        for port in self._ports:
            item = port['item']

            current_index = self._win.ports.itemWidget(item, 3).currentIndex()

            if current_index == 0:
                continue

            old_vlan_id = port['vlanid']
            new_vlan_id = self._vlans[current_index - 1]['vlanid']

            if new_vlan_id != old_vlan_id:
                self._set_config_thread.addJob(port['hostname'],
                                               port['interface'],
                                               old_vlan_id, new_vlan_id)

                text += '- Change port %s from vlan %s to vlan %s.\n' \
                        % (port['patchid'], old_vlan_id, new_vlan_id)

        if self._set_config_thread.jobCount() > 0 and \
            QMessageBox.question(self._win, "OK to submit?",
                                 "Submit the following changes?\n\n" + text,
                                 QMessageBox.Ok | QMessageBox.Cancel) == \
                                 QMessageBox.Ok:
            self._show_message('Submitting changes; please wait.')
            self._set_config_thread.start()
        else:
            self._set_config_thread.deleteLater()

    def _add_to_tree(self, port):
        ''' Add an entry for port <port> to the QTreeWidget, '''

        item = self._win.ports.invisibleRootItem()

        for id_segment in re.split('[_-]', port['patchid']):
            id_segment_to_index = { }

            for i in range(item.childCount()):
                segment_name = str(item.child(i).text(0))

                id_segment_to_index[segment_name] = i

            if id_segment in id_segment_to_index:
                child_index = id_segment_to_index[id_segment]
                child = item.child(child_index)
            else:
                child = QTreeWidgetItem(item, [ id_segment ])
                item.addChild(child)

            item = child

        item.setText(1, port['hostname'])
        item.setText(2, port['interface'])

        combo_box = MyComboBox(self._win.ports)

        combo_box.addItem('invalid')
        combo_box.addItems( [ vlan['label'] for vlan in self._vlans ] )

        try:
            label_index = self._vlan_id_to_label[port['vlanid']]
        except KeyError:
            combo_box.setCurrentIndex(0)
        else:
            combo_box.setCurrentIndex(label_index + 1)

        self._win.ports.setItemWidget(item, 3, combo_box)

        submit = QPushButton("Submit", self._win.ports)
        submit.clicked.connect(lambda checked, port = port, item = item:
                               self._submit_pressed(port, item))

        self._win.ports.setItemWidget(item, 4, submit)

        return item

if __name__ == '__main__':
    app = NewGui(sys.argv)

    sys.exit(app.exec_())
