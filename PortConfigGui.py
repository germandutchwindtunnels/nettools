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
""" This is the main file for the PortConfigGui application """

import portconfig

import sys
import os
from PyQt4 import QtGui, uic
from PyQt4.QtGui import QApplication, QPushButton, QComboBox, QTableWidgetItem, QCursor
from PyQt4.QtCore import QVariant, Qt

from OutputLog import OutLog

# For bugreporting at github
import webbrowser


class PortConfigGui(QtGui.QMainWindow):
    """ The main class/window for the PortConfigGui application """

    def __init__(self, hostname, username, password):
        self.username = username
        self.password = password
        self.hostname = hostname
        self.patchports = None
        self.vlans = None

        #super(PortConfigGui, self).__init__()
        QtGui.QMainWindow.__init__(self)

        install_dir = os.path.dirname(os.path.realpath(__file__))
        uic.loadUi(os.path.join(install_dir, 'PortConfigGui.ui'), self)
        self.statusbar.hide()

        self.buttonReload.clicked.connect(self._reload_data)
        self.buttonClearAll.clicked.connect(self._clear_pressed)
        self.buttonBugreport.clicked.connect(self.send_bug_report)
        self.buttonSubmitAll.clicked.connect(self._submit_all)
        self.setWindowTitle(self.windowTitle() + " " + self.hostname)

    def redirect_stdout(self):
        """ Redirect standard output to the QTextEdit """
        sys.stdout = OutLog(self.textEdit, sys.stdout)

    def redirect_stderr(self):
        """ Redirect standard error to the QTextEdit """
        sys.stderr = OutLog(self.textEdit, sys.stderr, QtGui.QColor(255, 0, 0))

    def load_patchports(self):
        """ Load all the patchports to self.patchports """
        while self.patchports is None:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            self.patchports = portconfig.get_available_patchports(
                self.hostname, 23, self.username, self.password)
            QApplication.restoreOverrideCursor()

    def load_vlans(self):
        """ Load all the VLANs """
        while self.vlans is None:
            self.vlans = portconfig.get_available_vlans(
                self.hostname, 23, self.username, self.password)

    def load_content(self):
        """ Load all contents """
        self.config_row(0)

    def append_row(self):
        """ Add a new row to the table """
        rowCount = self.tableWidget.rowCount()
        self.tableWidget.setRowCount(rowCount + 1)
        self.config_row(rowCount)

    def fillPatchports(self, comboBox):
        """ Fill the patchports into a ComboBox """
        comboBox.clear()
        # Fill out patchports
        self.load_patchports()
        for patchport in self.patchports:
            variantData = QVariant(str(patchport))
            label = patchport['patchid']
            comboBox.addItem(label, variantData)

    def fillVlans(self, comboBox):
        """ Fill the VLANs into a ComboBox """
        comboBox.clear()
        # Fill out vlans
        self.load_vlans()
        for vlan in self.vlans:
            variantData = QVariant(str(vlan))
            label = vlan['vlanid']  # vlan['vlanname'] + " (" + vlan['vlanid'] + ")"
            comboBox.addItem(label, variantData)

    def send_bug_report(self):  # pylint: disable=no-self-use
        """ Send a bug report """
        url = "https://github.com/germandutchwindtunnels/nettools/issues/new"
        webbrowser.open(url, 1, True)

    def _reload_data(self):
        """ Reload all data in the table """
        print "Reloading data..."
        self.vlans = None
        self.patchports = None
        self.load_vlans()
        self.load_patchports()
        self._clear_pressed()

    def config_row(self, row_number):
        """ Configure a row of the table """
        # Init all fields, this is needed to make all slots work when we fill everything out
        comboBoxPatchport = QComboBox(self.tableWidget)
        self.tableWidget.setCellWidget(row_number, 0, comboBoxPatchport)

        if row_number > 0:
            for i in range(1, 6):
                originalItem = self.tableWidget.item(row_number - 1, i)
                newItem = QTableWidgetItem(originalItem)
                self.tableWidget.setItem(row_number, i, newItem)

        comboBoxVlans = QComboBox(self.tableWidget)
        self.tableWidget.setCellWidget(row_number, 2, comboBoxVlans)

        buttonSubmit = QPushButton("Submit", self.tableWidget)
        buttonSubmit.setEnabled(False)
        self.tableWidget.setCellWidget(row_number, 6, buttonSubmit)

        # Connect selection signals
        comboBoxPatchport.currentIndexChanged.connect(
            lambda i, row_number=row_number: self._patchport_selected(row_number))
        comboBoxVlans.currentIndexChanged.connect(
            lambda i, row_number=row_number: self._vlanname_selected(row_number))
        buttonSubmit.clicked.connect(
            lambda i, row_number=row_number: self._submit_pressed(row_number))

        self.fillPatchports(comboBoxPatchport)
        self.fillVlans(comboBoxVlans)

        # Connect slots to add a row
        comboBoxVlans.currentIndexChanged.connect(
            lambda i, row_number=row_number: self._row_edited(row_number))
        comboBoxPatchport.currentIndexChanged.connect(
            lambda i, row_number=row_number: self._row_edited(row_number))

        # Resize
        self.tableWidget.resizeColumnsToContents()

    def _get_combobox_variantdata(self, row_number, column_number):
        """ Get the variantdata from a ComboBox """
        sourceComboBox = self.tableWidget.cellWidget(row_number, column_number)
        selectedIndex = sourceComboBox.currentIndex()

        variantData = sourceComboBox.itemData(selectedIndex)
        variantString = str(variantData.toString())
        variantDict = eval(variantString)  # pylint: disable=all
        return variantDict

    def _set_combobox_variantdata(self, row_number, column_number, variantdata):
        """ Set the variantdata of a ComboBox """
        sourceComboBox = self.tableWidget.cellWidget(row_number, column_number)
        selectedIndex = sourceComboBox.currentIndex()
        sourceComboBox.setItemData(selectedIndex, variantdata)

    def _patchport_selected(self, row_number):
        """ Qt slot for when a patchport was selected from a ComboBox """
        variantDict = self._get_combobox_variantdata(row_number, 0)

        print "Selected patchport %s on row %d..." % (str(variantDict), row_number)

        # Ports which are configured as dynamic may show up as "unassigned" when
        # nothing is connected
        if variantDict['vlanid'] == 'unassigned':
            variantDict['vlanid'] = 'dynamic'

        switchName = variantDict['hostname']
        switchPort = variantDict['interface']

        switchItem = self.tableWidget.item(row_number, 4)
        switchItem.setText(switchName)

        portItem = self.tableWidget.item(row_number, 5)
        portItem.setText(switchPort)

        comboBoxVlans = self.tableWidget.cellWidget(row_number, 2)
        comboBoxVlans.setCurrentIndex(comboBoxVlans.findText(variantDict['vlanid']))

    def _vlanname_selected(self, row_number):
        """ Qt slot for selecting a VLAN name from a ComboBox """
        variantDict = self._get_combobox_variantdata(row_number, 2)

        print "Selected vlan %s on row %d..." % (str(variantDict), row_number)

        vlanname = variantDict['vlanname']

        vlanIdItem = self.tableWidget.item(row_number, 3)
        vlanIdItem.setText(vlanname)

    def _row_edited(self, row_number):
        """ Qt slot for when a row was modified """
        submitButton = self.tableWidget.cellWidget(row_number, 6)
        submitButton.setEnabled(True)

        is_last_row = (self.tableWidget.rowCount() == (row_number + 1))
        if is_last_row:
            print "Adding new row..."
            self.append_row()

    def _submit_pressed(self, row_number):
        """ Qt slot for when a submit button was pressed """
        patchData = self._get_combobox_variantdata(row_number, 0)
        vlanData = self._get_combobox_variantdata(row_number, 2)

        username = self.username
        password = self.password
        switch_hostname = patchData['hostname']
        switchport = patchData['interface']
        old_vlanid = patchData['vlanid']
        vlanid = vlanData['vlanid']

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        portconfig.configure_patchid_raw(
            username, password, switch_hostname, switchport, vlanid, old_vlanid)
        QApplication.restoreOverrideCursor()

        patchData['vlanid'] = vlanid
        self._set_combobox_variantdata(row_number, 0, QVariant(str(patchData)))

    def _clear_pressed(self):
        """ Qt slot for clearing all rows """
        print "Clearing all rows..."
        self.tableWidget.setRowCount(1)
        self.config_row(0)

    def _submit_all(self):
        """ Qt slot for submitting all lines """
        print "Submit all..."
        rows = self.tableWidget.rowCount() - 1
        for row in range(0, rows):
            self._submit_pressed(row)


if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.stderr.write("Usage: " + sys.argv[0] + " username password first-hostname \n")
        sys.exit(-1)

    main_hostname = sys.argv[3]

    app = QApplication(sys.argv)
    pcg = PortConfigGui(main_hostname, sys.argv[1], sys.argv[2])
    pcg.show()
    pcg.redirect_stdout()
    pcg.redirect_stderr()
    print "Discovering network layout..."
    app.processEvents()
    pcg.load_content()
    sys.exit(app.exec_())
