import os
import re
from os.path import dirname, abspath

from src.api.Api import download
from PyQt5 import uic, QtCore
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QComboBox, QLabel, QLineEdit, QTableWidget, QProgressBar, \
    QTextBrowser
from PyQt5 import QtWidgets
import magic

from src.classes.Log import Log


class RhScreen(QWidget):
    app = None
    current_step = 1
    other_files = []
    job_id = None
    log = None

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
        self.job_summary = self.findChild(QTextBrowser, "job_summary")
        self.job_log = self.findChild(QTextBrowser, "job_log")

        self.host.addItem("Select Hosts", 0)
        self.software.addItem("Select Software", 0)

        self.software.currentIndexChanged.connect(self.software_selected)
        self.host.currentIndexChanged.connect(self.host_selected)

        # self.job_list.cellClicked.connect(self.download_report)

        self.job = {}

    def set_step(self, step):
        self.current_step = step

        for i in range(step + 1, 9):
            pxm = QPixmap("./src/gui/images/medium/%s.png" % i)
            self.steps[i].setPixmap(pxm)

        if step in self.steps:
            pixmap = QPixmap("./src/gui/images/medium/%s1.png" % step)
            self.steps[step].setPixmap(pixmap)

        for i in range(1, step):
            pxm = QPixmap("./src/gui/images/medium/%s2.png" % i)
            self.steps[i].setPixmap(pxm)

        # print("current step: ", self.current_step)

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

    def initializing(self):
        self.log = Log(self.app)
        self.log.info("Starting application", self.console)
        self.log.info("Retrieving job list", self.console)
        self.get_job_list()
        self.log.info("Retrieving Logs", self.console)
        self.get_job_logs()

        self.get_software_list()

    def get_software_list(self):
        self.log.info("Getting software list", self.console)
        sw = self.app.api.get("/software/list")
        for s in sw:
            # print(s)
            self.software.addItem(s['name'], s['id'])

    def get_job_logs(self):
        r = self.app.api.get("/host/logs")
        if r:
            self.job_log.clear()
            for j in r:
                try:
                    self.job_log.append("%s: %s\n"
                                        "Software: %s\n"
                                        "Status: %s\n"
                                        "Fee: $NT%s\n"
                                        "Duration: %s\n"
                                        "------------------------------------------------------------------------\n"
                                        % (j['start'], j['host_info'], j['software_name'], j['status'], j['cost'],
                                           j['duration']))
                except:
                    pass

    def software_selected(self):
        self.refresh()
        self.job_id = None
        software_id = self.software.itemData(self.software.currentIndex())

        if software_id:
            self.job['software_id'] = repr(software_id)

            self.log.info("Retrieving verified hosts", self.console)
            self.set_step(2)

            host = self.app.api.get("/software/%d/verified-hosts" % software_id)
            for h in host:
                self.host.addItem("$NT%s: %s" % (h['price'], h['host_info']), h['id'])

    def host_selected(self):
        if self.host.currentIndex() >= 0:
            self.job['host_id'] = self.host.itemData(self.host.currentIndex())
            self.refresh()
            self.set_step(4)
            self.job_id = None
            self.log.info("Host Selected", self.console)

    def get_job_info(self):
        if self.job_id:
            QtCore.QTimer.singleShot(2000, self.get_job_info)
            j = self.app.api.get("/job/%s/item" % self.job_id)
            self.log.debug("Job Info: %s" % j)
            self.job_summary.clear()
            self.get_job_logs()
            if j and 'status' in j:
                if j['status'] == 'completed':
                    self.set_step(8)
                    self.job_summary.append("Job finished!!")
                    self.job_summary.append("Software: %s" % j['software_name'])
                    self.job_summary.append("Host: %s" % j['host_info'])
                    self.job_summary.append("Fee: $%s" % j['price'])
                    self.job_summary.append("Started on: %s" % j['start'])
                    self.job_summary.append("Finished on: %s" % j['finish'])
                    self.job_summary.append("Duration: %s" % j['duration'])

    def get_job_list(self):
        QtCore.QTimer.singleShot(5000, self.get_job_list)
        self.job_list.setRowCount(0)
        jobs = self.app.api.get("/job/list")
        row = 0
        for j in jobs:
            # print(j)
            self.job_list.insertRow(self.job_list.rowCount())

            self.job_list.setItem(row, 0, QtWidgets.QTableWidgetItem("%s" % j['id']))
            self.job_list.setItem(row, 1, QtWidgets.QTableWidgetItem(j['created_at']))
            self.job_list.setItem(row, 2, QtWidgets.QTableWidgetItem(j['software_name']))
            self.job_list.setItem(row, 3, QtWidgets.QTableWidgetItem(j["host_info"]))
            self.job_list.setItem(row, 4, QtWidgets.QTableWidgetItem("$NT%s" % j['price']))
            self.job_list.setItem(row, 5, QtWidgets.QTableWidgetItem(j['status']))

            if j['status'] == 'completed':
                dl = QtWidgets.QPushButton()
                dl.setIcon(QIcon("./src/gui/images/medium/download.png"))
                dl.clicked.connect(self.download_report)
                self.job_list.setCellWidget(row, 6, dl)

            elif j['status'] == 'pending':
                stop = QtWidgets.QPushButton()
                stop.setIcon(QIcon("./src/gui/images/medium/stop.png"))
                stop.clicked.connect(self.stop_job)
                self.job_list.setCellWidget(row, 6, stop)
                pass

            elif j['status'] == 'stopped':
                start = QtWidgets.QPushButton()
                start.setIcon(QIcon("./src/gui/images/medium/start.png"))
                start.clicked.connect(self.start_job)
                self.job_list.setCellWidget(row, 6, start)

                pass

            row += 1

        # item = QtWidgets.QTableWidgetItem("test3")
        # self.job_list.setVerticalHeaderItem(self.job_list.rowCount() - 1, item)

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

            self.log.info("Run file selected %s" % fileName, self.console)
            content_type = self.mime.from_file(fileName)
            self.job['run_file'] = (os.path.basename(fileName), open(fileName, 'rb'), content_type)
            self.refresh()
            self.set_step(3)
            self.job_id = None

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
                self.log.info("Other files selected: %s" % file, self.console)
                content_type = self.mime.from_file(file)
                self.job['other_files[%d]' % k] = (os.path.basename(file), open(file, 'rb'), content_type)
                k += 1

        self.job_id = None

    def submit_job(self):
        if self.job_id:
            self.start_job(self.job_id)
        elif self.current_step == 4:
            self.set_step(5)
            self.log.info("Creating job", self.console)

            r = self.app.api.upload("/job/create", self.job, self.monitor)
            # self.get_job_list()

            if r:
                self.log.debug(r)
                self.log.info("Job submitted", self.console, True)
                self.job_id = r['id']
                self.get_job_info()
                self.get_job_list()

        pass

    def monitor(self, monitor):
        percent = round((monitor.bytes_read / monitor.len) * 100)
        self.upload_bar.setValue(percent)
        if percent == 100:
            self.log.info("File successfully transferred", self.console)
            self.set_step(6)
        pass

    def clear_form(self):
        # clear software
        self.software.clear()
        self.software.addItem("Select Software", 0)

        # clear host
        self.host.clear()
        self.host.addItem("Select Hosts", 0)
        self.job['host_id'] = None

        # clear files
        self.run_file.clear()
        self.job['run_file'] = None

        # clear other files
        self.other_files.clear()
        self.job['other_files'] = None

        self.get_software_list()

    def start_job(self, job_id=None):
        if job_id is None and self.job_id:
            job_id = self.job_id

        job_id = self.get_job_id_from_button(job_id)

        if job_id:
            print("start job id: %s" % job_id)
            r = self.app.api.post("/job/%s/start" % job_id)
            print(r)
            if r:
                self.log.info("Job started", self.console)

    def stop_job(self, job_id=None):
        if not job_id and self.job_id:
            job_id = self.job_id

        job_id = self.get_job_id_from_button(job_id)

        print(job_id)

        if job_id:
            print("stop job id: %s" % job_id)
            r = self.app.api.post("/job/%s/stop" % job_id)
            print(r)
            if r:
                self.log.info("Job stopped", self.console)
        pass

    def download_report(self, job_id):

        job_id = self.get_job_id_from_button(job_id)

        # job_id = self.job_list.item(row, 0)
        # print("Selected Job ID %s" % job_id.text())
        j = self.app.api.get("/job/%s/download_report" % job_id)

        if j:
            report = download(j['file_url'])
            f = re.findall(r"(\w+).zip$", j['file_url'])

            path = self.app.home_dir + "/reports/" + f[0]
            file_name = path + '.zip'
            open(file_name, "wb").write(report)
            self.log.info("Report file has been saved at %s" % file_name, self.console, True)
            self.clear_form()
            self.set_step(9)

    def get_job_id_from_button(self, job_id):
        if not job_id:
            button = self.app.main.focusWidget()
            # or button = self.sender()
            index = self.job_list.indexAt(button.pos())
            if index.isValid():
                job_id = self.job_list.item(index.row(), 0)
                if job_id is not None:
                    job_id = job_id.text()

        return job_id
