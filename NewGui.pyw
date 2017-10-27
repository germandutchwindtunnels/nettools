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

""" A New GUI for nettools. """

import sys
import re
import webbrowser
# import pprint

import portconfig

from PyQt4.QtGui import QApplication, QMessageBox, QTreeWidgetItem, QComboBox, QCheckBox
from PyQt4.QtGui import QPushButton, QPalette, QColor, QIcon, QLabel
from PyQt4.QtGui import QTextBrowser, QVBoxLayout, QFrame
from PyQt4.QtCore import QThread, pyqtSignal, QVariant, QSettings
import PyQt4.uic as uic
import json
import os.path
import ctypes
import os
import multiprocessing
from Cisco import CiscoTelnetSession


def execute_custom(hostname, port, username, password, command):
    print "Executing " + command + " on " + hostname
    device = CiscoTelnetSession()
    open_result = device.open(hostname, port, username, password)
    ret = {}
    ret[hostname] = device.execute_command(command)
    return ret


class WorkerThread(QThread):
    """ Perform a background job. Emits a "finished" signal when done. """

    def __init__(self, username, password):
        """ Initialisation. """

        QThread.__init__(self)

        self._user = username
        self._pass = password


class GetConfigurationThread(WorkerThread):
    """ Get the network configuration in the background. Emits the "newData"
        signal with patchports and vlans when done, then emits the "finished"
        signal. """

    newData = pyqtSignal(dict)

    def __init__(self, hostname, username, password):
        """ Initialisation. """

        WorkerThread.__init__(self, username, password)

        self._host = hostname

    def run(self):
        """ Run this thread. """

        data = {
            'ports': portconfig.get_available_patchports(self._host, 23,
                                                         self._user,
                                                         self._pass),
            'vlans': portconfig.get_available_vlans(self._host, 23,
                                                    self._user,
                                                    self._pass),
            'health': portconfig.get_health_status(self._host, 23,
                                                   self._user,
                                                   self._pass)
        }

        self.newData.emit(data)


class SetConfigurationThread(WorkerThread):
    """ Set the network configuration in the background. Emits the "finished"
        signal when done. """

    def __init__(self, username, password):
        WorkerThread.__init__(self, username, password)

        self._jobs = []

    def addJob(self, switch_host, switch_port, old_vlan_id, new_vlan_id):
        """ Add a job configuring <switch_port> on <switch_host> from
            <old_vlan_id> to <new_vlan_id>. """

        self._jobs.append({
            'switch_host': switch_host,
            'switch_port': switch_port,
            'old_vlan_id': old_vlan_id,
            'new_vlan_id': new_vlan_id
        })

    def jobCount(self):
        """ Return the number of jobs defined for this thread. """

        return len(self._jobs)

    def run(self):
        """ Run this thread. """

        for job in self._jobs:
            portconfig.configure_patchid_raw(self._user, self._pass,
                                             job['switch_host'],
                                             job['switch_port'],
                                             job['new_vlan_id'],
                                             job['old_vlan_id'])

        self._jobs = []


class MyComboBox(QComboBox):
    """ A subclass of the PyQt4 QComboBox that ignores mouse wheel events. """

    def wheelEvent(self, event):    # pylint: disable=no-self-use
        """ Pass through mouse wheel events, so they scroll the underlying table
            instead of this combo box. """

        event.ignore()

    def fill(self, data):
        """ Fill this combobox with <data>, which is a list of entries, each
            consisting of a tuple with a vlan number and a string. The string is
            used as the label, the vlan number as the associated data. """

        assert isinstance(data, list)

        self.clear()

        for i, (vlan, label) in enumerate(data):
            self.addItem(str(label))
            self.setItemData(i, vlan)

    def selectData(self, data):
        """ Select the entry that has data field <data>. """

        index = self.findData(QVariant(data))

        if index == self.currentIndex():
            return
        elif index == -1:
            self.selectData(None)
        else:
            self.setCurrentIndex(index)

    def itemData(self, index):
        """ Return the data field associated with the <index>'th field. """

        variant = QComboBox.itemData(self, index)

        if variant.type() == QVariant.Int:
            return variant.toInt()[0]
        elif variant.type() == QVariant.String:
            return str(variant.toString())
        else:
            return None

    def currentData(self):
        """ Return the data field associated with the currently selected field.
        """

        return self.itemData(self.currentIndex())


class NewGui(QApplication):
    """ Port Configurator GUI. """

    COL_PATCH = 0
    COL_STATUS = 0
    COL_SWITCH = 1
    COL_DETAILS = 2
    COL_PORT = 2
    COL_VLAN = 3
    COL_COMBO = 4
    COL_SUBMIT = 5

    OK_COLOR = 'none'
    WARN_COLOR = '#FFA500'
    ERR_COLOR = '#FF0000'
    textboxes = {}
    checkboxes = {}

    def __init__(self, args):
        """ Initialisation. """

        QApplication.__init__(self, args)

        self._ports = []
        self._vlans = []
        self._health = []

        self._msg_box = None

        self._labels = []

        self._changes = []

        self._get_config_thread = None
        self._set_config_thread = None

        self._win = uic.loadUi("Login.ui")

        # Get credentials from persistent storage

        self._qsettings = QSettings("DNW", "nettools", self)

        self._win.RememberCheck.setChecked(self._qsettings.childKeys().count() > 0)

        if self._qsettings.contains('username'):
            self._win.UserName.setText(self._qsettings.value('username').toString())
        if self._qsettings.contains('password'):
            self._win.Password.setText(self._qsettings.value('password').toString())
        if self._qsettings.contains('hostname'):
            self._win.HostName.setText(self._qsettings.value('hostname').toString())

        self._win.LoginButton.clicked.connect(self._login)
        self._win.UserName.returnPressed.connect(self._win.LoginButton.click)
        self._win.Password.returnPressed.connect(self._win.LoginButton.click)
        self._win.HostName.returnPressed.connect(self._win.LoginButton.click)

        self._win.show()

    def _login(self):
        self._win.errorBox.document().setPlainText("")
        self._win.errorBox.setStyleSheet('background: %s;' % self.OK_COLOR)

        QApplication.processEvents()

        self._user = str(self._win.UserName.text())
        self._pass = str(self._win.Password.text())
        self._host = str(self._win.HostName.text())
        self._rememberCheck = self._win.RememberCheck.isChecked()

        if(self._host == "" or self._user == "" or self._pass == ""):
            self._win.errorBox.document().setPlainText("Please make sure to fill in all the variables")
            self._win.errorBox.setStyleSheet('background: %s;' % self.ERR_COLOR)
            return

        if self._rememberCheck:         # Save credentials to persistent storage
            self._qsettings.setValue('username', self._user)
            self._qsettings.setValue('password', self._pass)
            self._qsettings.setValue('hostname', self._host)
        else:                           # Clear persistent storage
            self._qsettings.clear()

        self._qsettings.sync()

        self._win = uic.loadUi("NewGui.ui")
        self._win.ports.itemExpanded.connect(lambda item: self._resize())
        self._win.ports.itemCollapsed.connect(lambda item: self._resize())
        self._win.Health.itemExpanded.connect(lambda item: self._resize())
        self._win.Health.itemCollapsed.connect(lambda item: self._resize())

        self._win.buttonReload.clicked.connect(self._get_configuration)
        self._win.buttonSubmitAll.clicked.connect(self._submit_all)
        self._win.buttonBugReport.clicked.connect(self._report_bug)

        self._win.statusbar.hide()
        self._win.ports.hideColumn(NewGui.COL_VLAN)

        self._win.show()

        self._get_configuration()

    def _handle_new_data(self, data):
        """ Handle data from the GetConfigurationThread. """

        self._ports = data['ports']
        self._vlans = data['vlans']
        self._health = data['health']

        self._labels = [(None, u'invalid')]

        for vlan in self._vlans:
            vlanid = vlan['vlanid']
            label = '%s (%s)' % (vlanid, vlan['vlanname'])

            self._labels.append((vlanid, label))

        for i, port in enumerate(self._ports):
            if port['vlanid'] == 'unassigned':
                self._ports[i]['vlanid'] = 'dynamic'

        # print "Ports:"
        # pprint.pprint(self._ports)

        # print "VLANs:"
        # pprint.pprint(self._vlans)

        self._refresh()

    def _get_config_thread_finished(self):
        """ Handle completion of the GetConfigurationThread. """

        self._get_config_thread.deleteLater()

        if self._msg_box:
            self._msg_box.hide()
            self._msg_box.deleteLater()
            self._msg_box = None

        scroll_area = self._win.scrollAreaWidgetContents
        scroll_area.setMinimumHeight(150 * len(portconfig.switchlist.seen))

        splitter = self._win.splitter

        for host in portconfig.switchlist.seen:
            container_widget = QFrame(scroll_area)
            container_widget.setFrameStyle(QFrame.Panel | QFrame.Sunken)

            container_layout = QVBoxLayout(container_widget)

            self.checkboxes[host] = QCheckBox(host, container_widget)
            self.textboxes[host] = QTextBrowser(container_widget)
            self.textboxes[host].setMinimumHeight(1)

            container_layout.addWidget(self.checkboxes[host])
            container_layout.addWidget(self.textboxes[host])

            splitter.addWidget(container_widget)

        self._win.ConsoleInput.returnPressed.connect(self._sendToAll)

    def _sendToAll(self):
        ExecuteOn = []
        command = str(self._win.ConsoleInput.text())
        cpu_count = 25  # multiprocessing.cpu_count()
        print >>sys.stderr, "Process count %d" % cpu_count
        for host, cb in enumerate(self.checkboxes):
            if self.checkboxes[cb].isChecked():
                print "Execute on " + cb
                ExecuteOn.append(cb)
        pool = multiprocessing.Pool(processes=cpu_count)
        results = []
        for host in ExecuteOn:
            results.append(pool.apply_async(
                execute_custom, (host, 23, self._user, self._pass, command)))
        pool.close()
        pool.join()
        results = [r.get() for r in results]
        for host in results:
            self.textboxes[host.keys()[0]].setText(host[host.keys()[0]])

    def _show_message(self, text):
        """ Show an informational message box with <text>. """

        self._msg_box = QMessageBox(self._win)

        self._msg_box.setIcon(QMessageBox.Information)
        self._msg_box.setWindowTitle("Working...")
        self._msg_box.setText(text)

        self._msg_box.setStandardButtons(QMessageBox.NoButton)

        self._msg_box.show()

    def _get_configuration(self):
        """ Get the current network configuration. """

        self._win.ports.clear()

        self._show_message('Getting switch configuration; please wait.')

        self._get_config_thread = GetConfigurationThread(self._host,
                                                         self._user,
                                                         self._pass)
        self._get_config_thread.newData.connect(self._handle_new_data)
        self._get_config_thread.finished.connect(self._get_config_thread_finished)
        self._get_config_thread.start()

    def _resize(self):
        """ Resize the columns of the data table based on its current contents.
        """

        for col in range(self._win.ports.columnCount()):
            self._win.ports.resizeColumnToContents(col)
        for col in range(self._win.Health.columnCount()):
            self._win.Health.resizeColumnToContents(col)

    def _refresh(self):
        """ Refresh the data table based on the current data. """

        self._win.ports.clear()
        self._win.Health.clear()

        for index, port in enumerate(self._ports):
            self._ports[index]['item'] = self._add_to_tree(port)

        for index, health in enumerate(self._health):
            self._health[index]['item'] = self._add_to_health(health)

        self._resize()

    def _reset_children(self, item):
        """ Reset the current vlan number and disable the Submit button for all
            the child items below <item>. """

        for index in range(item.childCount()):
            child = item.child(index)

            if child.childCount() == 0:
                new_vlan_id = str(self._win.ports.itemWidget(child,
                                                             NewGui.COL_COMBO).currentData())
                child.setText(NewGui.COL_VLAN, new_vlan_id)

                button = self._win.ports.itemWidget(child, NewGui.COL_SUBMIT)
                button.setEnabled(False)
            else:
                self._reset_children(child)

    def _set_config_thread_finished(self):
        """ Handle completion of the SetConfigurationThread. """

        self._set_config_thread.deleteLater()

        if self._msg_box:
            self._msg_box.hide()
            self._msg_box.deleteLater()
            self._msg_box = None

        self._reset_children(self._win.ports.invisibleRootItem())

        self._changes = []

        self._win.buttonSubmitAll.setEnabled(False)

    def _vlan_selected(self, index, item):
        """ The user selected the vlan number with index <index> in the combo
            box for QTreeWidgetItem <item>. """

        vlan_combo = self._win.ports.itemWidget(item, NewGui.COL_COMBO)
        submit_button = self._win.ports.itemWidget(item, NewGui.COL_SUBMIT)

        cur_vlan = str(item.text(NewGui.COL_VLAN))
        new_vlan = str(vlan_combo.itemData(index))

        submit_button.setEnabled(new_vlan != cur_vlan)

        if new_vlan == cur_vlan and item in self._changes:
            self._changes.remove(item)
        elif new_vlan != cur_vlan and item not in self._changes:
            self._changes.append(item)

        self._win.buttonSubmitAll.setEnabled(len(self._changes) > 0)

    def _submit_pressed(self, port, item):
        """ The user has pressed the Submit button for <port> in QTreeWidgetItem
            <item>. Handle this."""

        switch_host = port['hostname']
        switch_port = port['interface']
        old_vlan_id = str(item.text(NewGui.COL_VLAN))
        new_vlan_id = str(self._win.ports.itemWidget(item,
                                                     NewGui.COL_COMBO).currentData())

        self._show_message('Setting port %s to vlan %s; please wait.' %
                           (port['patchid'], new_vlan_id))

        self._set_config_thread = SetConfigurationThread(self._user, self._pass)
        self._set_config_thread.addJob(switch_host, switch_port,
                                       old_vlan_id, new_vlan_id)
        self._set_config_thread.finished.connect(
            self._set_config_thread_finished)
        self._set_config_thread.start()

    def _submit_all(self):
        """ The user has pressed the "Submit all" button. Handle this. """

        self._set_config_thread = SetConfigurationThread(self._user, self._pass)
        self._set_config_thread.finished.connect(self._set_config_thread_finished)

        text = ""

        for port in self._ports:
            item = port['item']

            current_data = self._win.ports.itemWidget(item,
                                                      NewGui.COL_COMBO).currentData()

            if current_data is None:
                continue

            old_vlan_id = str(item.text(NewGui.COL_VLAN))
            new_vlan_id = str(current_data)

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

    @staticmethod
    def _report_bug():
        """ Direct the user to github to create a bug report. """

        url = "https://github.com/germandutchwindtunnels/nettools/issues/new"

        webbrowser.open(url, 1, True)

    def _add_to_health(self, health):
        """ Add an entry for health <health> to the QTreeWidget, """

        item = self._win.Health.invisibleRootItem()

        child = QTreeWidgetItem(item, ["", health['hostname'], ""])

        color = "green"

        for index, status in health.items():
            if index == "TEMPSTATUS":
                string = "Temperature Status"
            if index == "FAN":
                string = "Fan Status"
            if index == "TEMPCOLOR":
                string = "Temperature Color"
            if index == "TEMP":
                string = "Temperature"
            if index == "hostname":
                continue

            if status is not None:
                subchild = QTreeWidgetItem(child, ["", string, status])
                if status == 'OK':
                    subchild.setIcon(0, QIcon('./green.png'))
                elif status == "GREEN":
                    subchild.setIcon(0, QIcon('./green.png'))
                elif index == "TEMP":
                    # We have a numeric value
                    if int(status) < 60:
                        subchild.setIcon(0, QIcon('./green.png'))
                    else:
                        subchild.setIcon(0, QIcon('./red.png'))
                        color = "red"
                else:
                    color = "red"
                    subchild.setIcon(0, QIcon('./red.png'))
                child.addChild(subchild)

        child.setIcon(0, QIcon('./' + color + '.png'))
        item.addChild(child)
        return item

    def _add_to_tree(self, port):
        """ Add an entry for port <port> to the QTreeWidget. """

        # Start at the root of the tree.
        item = self._win.ports.invisibleRootItem()

        # Split the patch id into segments, and for every segment...
        for id_segment in re.split('[_-]', port['patchid']):
            id_segment_to_index = {}

            # Get the names of all the child items at the current tree level...
            for i in range(item.childCount()):
                segment_name = str(item.child(i).text(NewGui.COL_PATCH))

                id_segment_to_index[segment_name] = i

            # If there already is a child item for this segment...
            if id_segment in id_segment_to_index:
                # then select that child to follow,
                child_index = id_segment_to_index[id_segment]
                child = item.child(child_index)
            else:
                # otherwise create and select a new child.
                child = QTreeWidgetItem(item, [id_segment])
                item.addChild(child)

            # Make the selected child the current item and do it all again.
            item = child

        item.setText(NewGui.COL_SWITCH, port['hostname'])
        item.setText(NewGui.COL_PORT, port['interface'])
        item.setText(NewGui.COL_VLAN, port['vlanid'])

        combo_box = MyComboBox(self._win.ports)

        combo_box.fill(self._labels)
        combo_box.selectData(port['vlanid'])

        self._win.ports.setItemWidget(item, NewGui.COL_COMBO, combo_box)

        combo_box.currentIndexChanged.connect(
            lambda index, item=item: self._vlan_selected(index, item))

        submit = QPushButton("Submit", self._win.ports)
        submit.clicked.connect(
            lambda checked, port=port, item=item:
            self._submit_pressed(port, item))

        submit.setEnabled(False)

        self._win.ports.setItemWidget(item, NewGui.COL_SUBMIT, submit)

        return item


if __name__ == '__main__':
    app = NewGui(sys.argv)

    sys.exit(app.exec_())
