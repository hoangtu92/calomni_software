import os
import re
import threading
from datetime import datetime
from os.path import dirname, abspath

import requests
from PyQt5 import uic, Qt, QtCore
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QComboBox, QLabel, QLineEdit, QTableWidget, QProgressBar, \
    QTextBrowser
from PyQt5 import QtWidgets
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
import magic

from src.classes.Alert import Alert


class RhScreen(QWidget):
    app = None
    current_step = 1
    other_files = []
    job_id = None

    def __init__(self, app):
        self.app = app
        QWidget.__init__(self)

        self.mime = magic.Magic(mime=True)

        uic.loadUi(dirname(dirname(abspath(__file__))) + "/gui/rh_screen.ui", self)
        cp = QDesktopWidget().availableGeometry().center()
        qr = self.frameGeometry()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.steps = {
            1: self.findChild(QLabel, "step1"),
            2: self.findChild(QLabel, "step2"),
            3: self.findChild(QLabel, "step3"),
            4: self.findChild(QLabel, "step4"),
            5: self.findChild(QLabel, "step5"),
            6: self.findChild(QLabel, "step6"),
            7: self.findChild(QLabel, "step7"),
            8: self.findChild(QLabel, "step8"),
        }

        self.set_step(1)

        self.software = self.findChild(QComboBox, "software")
        self.run_file = self.findChild(QLineEdit, "run_file")
        self.other_files = self.findChild(QLineEdit, "other_files")
        self.host = self.findChild(QComboBox, "hosts")
        self.job_list = self.findChild(QTableWidget, "job_list")
        self.upload_bar = self.findChild(QProgressBar, "upload_bar")
        self.console = self.findChild(QTextBrowser, "console")

        self.log("Starting application")

        self.host.addItem("Select Hosts", 0)
        self.software.addItem("Select Software", 0)

        self.software.currentIndexChanged.connect(self.software_selected)
        self.host.currentIndexChanged.connect(self.host_selected)

        self.job_list.cellClicked.connect(self.download_report)

        self.job = {}

    def set_step(self, step):
        self.current_step = step

        for i in range(step + 1, 9):
            pxm = QPixmap("./src/gui/images/medium/%s.png" % i)
            self.steps[i].setPixmap(pxm)

        pixmap = QPixmap("./src/gui/images/medium/%s1.png" % step)
        self.steps[step].setPixmap(pixmap)

        for i in range(1, step):
            pxm = QPixmap("./src/gui/images/medium/%s2.png" % i)
            self.steps[i].setPixmap(pxm)

        print("current step: ", self.current_step)

    def refresh(self):

        if self.software.itemData(self.software.currentIndex()) == 0:
            self.set_step(1)
        else:
            if self.run_file.text() == "":
                self.set_step(2)
            else:
                if self.host.itemData(self.host.currentIndex()) == 0:
                    self.set_step(3)
                else:
                    if self.job_id is None:
                        self.set_step(4)
                    else:
                        self.set_step(5)

    def get_data(self):
        self.log("Getting software list")
        sw = self.app.api.get("/software/list")
        self.get_job_list()
        for s in sw:
            # print(s)
            self.software.addItem(s['name'], s['id'])

    def software_selected(self):
        self.refresh()
        software_id = self.software.itemData(self.software.currentIndex())

        self.job['software_id'] = repr(software_id)

        self.host.clear()
        self.host.addItem("Select Hosts", 0)

        self.log("Retrieving verified hosts")
        host = self.app.api.get("/software/%d/verified-hosts" % software_id)
        for h in host:
            print(h)
            self.host.addItem("$NT%s: %s" % (h['price'], h['info']), h['id'])

    def host_selected(self):
        if self.host.currentIndex() >= 0:
            self.job['host_id'] = self.host.itemData(self.host.currentIndex())
        self.refresh()
        self.log("Host Selected")

    def get_job_list(self):
        QtCore.QTimer.singleShot(5000, self.get_job_list)
        self.job_list.setRowCount(0)
        self.log("Retrieving job list")
        jobs = self.app.api.get("/job/list")
        idx = 1
        for j in jobs:
            # print(j)
            self.job_list.insertRow(self.job_list.rowCount())

            self.job_list.setItem(self.job_list.rowCount() - 1, 0, QtWidgets.QTableWidgetItem("%s" % j['id']))
            self.job_list.setItem(self.job_list.rowCount() - 1, 1, QtWidgets.QTableWidgetItem(j['created_at']))
            self.job_list.setItem(self.job_list.rowCount() - 1, 2, QtWidgets.QTableWidgetItem(j['software_name']))
            self.job_list.setItem(self.job_list.rowCount() - 1, 3, QtWidgets.QTableWidgetItem(j["host_info"]))
            self.job_list.setItem(self.job_list.rowCount() - 1, 4, QtWidgets.QTableWidgetItem("$NT%s" % j['price']))
            self.job_list.setItem(self.job_list.rowCount() - 1, 5, QtWidgets.QTableWidgetItem(j['status']))

            download = QtWidgets.QTableWidgetItem()
            download.setIcon(QIcon("./src/gui/images/medium/download.png"))
            self.job_list.setItem(self.job_list.rowCount() - 1, 6, download)
            idx += 1

        # item = QtWidgets.QTableWidgetItem("test3")
        # self.job_list.setVerticalHeaderItem(self.job_list.rowCount() - 1, item)

    def download_report(self, row, col):

        if col != 6:
            return

        job_id = self.job_list.item(row, 0)
        print("Selected Job ID %s" % job_id.text())
        j = self.app.api.get("/job/%s/download_report" % job_id.text())

        if j:
            print(j)
            r = requests.get(j['file_url'], allow_redirects=True)
            f = re.findall(r"(\w+).zip$", j['file_url'])

            if not os.path.isdir(self.app.home_dir + "/reports/"):
                os.mkdir(self.app.home_dir + "/reports/")

            path = self.app.home_dir + "/reports/" + f[0]
            file_name = path + '.zip'
            open(file_name, "wb").write(r.content)
            self.log("Report file has been saved at %s" % file_name)

    def browse_file(self):

        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "QFileDialog.getOpenFileName()",
            "",
            "All Files (*);;Python Files (*.py)",
            options=options)
        if fileName:
            # print(fileName)
            self.run_file.setText(fileName)

            self.log("Run file selected %s"%fileName)
            content_type = self.mime.from_file(fileName)
            self.job['run_file'] = (os.path.basename(fileName), open(fileName, 'rb'), content_type)
            self.refresh()

    def browse_files(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_names, _ = QtWidgets.QFileDialog.getOpenFileNames(
            None,
            "QFileDialog.getOpenFileName()",
            "",
            "All Files (*);;Python Files (*.py)",
            options=options)
        if file_names:
            # print(fileNames)
            self.other_files.setText(file_names[0])
            k = 0
            for file in file_names:
                self.log("Other files selected: %s" % file)
                content_type = self.mime.from_file(file)
                self.job['other_files[%d]' % k] = (os.path.basename(file), open(file, 'rb'), content_type)
                k += 1

    def submit_job(self):
        if self.current_step == 4 or 1:
            self.set_step(5)
            self.log("Creating job")
            m = MultipartEncoder(fields=self.job)

            monitor = MultipartEncoderMonitor(m, self.monitor)

            r = self.app.api.upload("/job/create", monitor)
            # self.get_job_list()

            if r:
                self.log("Job submitted")
                self.job_id = r['id']
                Alert("Job Submitted!")
        pass

    def monitor(self, monitor):
        percent = round((monitor.bytes_read / monitor.len)*100)
        self.upload_bar.setValue(percent)
        if percent == 100:
            self.log("File successfully transferred")
            self.set_step(6)
        pass

    def stop_job(self):
        self.log("Job stopped")
        pass

    def log(self, msg):
        today = datetime.now()
        date = today.strftime("%Y/%m/%d %H:%M:%S")
        self.console.append("%s %s" % (date, msg))

    def download_job_result(self):
        pass
