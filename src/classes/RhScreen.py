import json
import os
import re
import queue
import threading
from os.path import dirname, abspath
from zipfile import ZipFile

import pycurl
from PyQt5.QtCore import QSize, QTimer
from src.api.Api import download
from PyQt5 import uic, QtCore
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QComboBox, QLabel, QLineEdit, QTableWidget, QProgressBar, \
    QTextBrowser
from PyQt5 import QtWidgets
import magic

from src.api.Pusher import pusherClient, pusherServer, job_channel
from src.classes.Helper import Helper
from src.classes.Log import Log


class RhScreen(QWidget):
    app = None
    current_step = 1
    other_files = []
    job_id = None
    log = None
    upload_bar = None
    is_cancel_upload = False
    current_job = None
    callback_queue = queue.Queue()
    timer = QTimer()
    emitter = QtCore.pyqtSignal(object)
    online_hosts = []

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

        self.job = {}

        self.emitter.connect(self.on_event_callback)

    def initializing(self):
        self.log = Log(self.app)
        self.log.info("Starting application", self.console)

        pusherClient.connection.bind('pusher:connection_established', self.connection_handler)

        threading.Thread(target=self.get_job_list).start()
        threading.Thread(target=self.get_job_logs).start()
        threading.Thread(target=self.get_software_list).start()

    def connection_handler(self, event=None):
        event = json.loads(event)
        print(event)
        if event["socket_id"]:
            self.app.socket_id = str(event["socket_id"])
            self.init_pusher()
        else:
            pusherClient.connect()

    def init_pusher(self):
        channel = pusherClient.subscribe(job_channel)
        channel.bind("pusher_internal:subscription_succeeded", self.subscription_succeeded)
        channel.bind("pusher_internal:member_added", self.member_added)
        channel.bind("pusher_internal:member_removed", self.member_removed)
        channel.bind(self.app.token + '.job_completed', self.job_handle)
        channel.bind(self.app.token + '.job_running', self.job_handle)

    def subscription_succeeded(self, event):
        event  = json.loads(event)
        print("subscription_succeeded", event)
        self.online_hosts = event["presence"]["ids"]
        self.emitter.emit({"action": "member_online", "data": event})

    def member_removed(self, event):
        print("Member Removed", event)
        member = json.loads(event)
        del self.online_hosts[self.online_hosts.index(member["user_id"])]
        self.emitter.emit({"action": "member_online", "data": member})

    def member_added(self, event):
        print("Member Added", event)
        member = json.loads(event)
        self.online_hosts.append(member["user_id"])
        self.emitter.emit({"action": "member_online", "data": member})

    def job_handle(self, event):
        print("Job status changed", event)
        event = json.loads(event)
        self.emitter.emit({"action": "job_status", "data": event})

    @QtCore.pyqtSlot(object)
    def on_event_callback(self, event):
        print("Internal Event", event)
        data = event["data"]
        if event["action"] == "member_online" or event["action"] == "job_status" or event["action"] == "job_list":
            self.show_job_list(event)
        if event["action"] == "job_log":
            self.job_log.clear()
            for j in data:
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

        if event["action"] == "software_list":
            self.clear_software()
            for s in data:
                # print(s)
                self.software.addItem(s['name'], s['id'])


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

    def get_software_list(self):
        sw = self.app.api.get("/software/list")
        if sw:
            self.emitter.emit({"action": "software_list", "data": sw})

    def get_job_logs(self):
        r = self.app.api.get("/host/logs")
        if r:
            self.emitter.emit({"action": "job_log", "data": r})

    def software_selected(self):
        self.refresh()
        self.job_id = None
        software_id = self.software.itemData(self.software.currentIndex())

        if software_id:
            self.job['software_id'] = repr(software_id)

            self.log.info("Retrieving verified hosts", self.console)
            self.set_step(2)

            self.get_hosts(software_id)

    def get_hosts(self, software_id):
        host = self.app.api.get("/software/%d/verified-hosts" % software_id)
        if host:
            self.clear_host()
            for h in host:
                status = "INACTIVE"
                if h["token"] in self.online_hosts:
                    status = "ACTIVE"
                self.host.addItem("$NT%s: [%s] %s" % (h['price'], status, h['host_info']), h['id'])

    def host_selected(self):
        if self.host.currentIndex() >= 0:
            self.job['host_id'] = self.host.itemData(self.host.currentIndex())
            self.refresh()
            self.set_step(4)
            self.job_id = None
            self.log.info("Host Selected", self.console)

    def get_job_info(self):
        if self.job_id:
            j = self.app.api.get("/job/%s/item" % self.job_id)
            # self.log.debug("Job Info: %s" % j)
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
        jobs = self.app.api.get("/job/list")
        self.emitter.emit({"action": "job_list", "data": jobs})

    def show_job_list(self, args=None):
        self.job_list.setRowCount(0)
        row = 0
        for j in args["data"]:
            self.job_list.insertRow(self.job_list.rowCount())

            if "created_at" in j:
                self.job_list.setItem(row, 0, QtWidgets.QTableWidgetItem(j['created_at']))
            if "software_name" in j:
                self.job_list.setItem(row, 1, QtWidgets.QTableWidgetItem(j['software_name']))
            if "host_info" in j:

                g = QtWidgets.QWidget()
                l = QtWidgets.QHBoxLayout()

                s = QtWidgets.QLabel()

                g.setToolTip(j["host_info"])
                g.setToolTipDuration(600000)

                if j['host_activity_status'] == 'active' or j["sh_token"] in self.online_hosts:
                    pxm = QPixmap("./src/gui/images/medium/online.png")
                    s.setPixmap(pxm.scaled(8, 8, QtCore.Qt.KeepAspectRatio))
                else:
                    pxm = QPixmap("./src/gui/images/medium/offline.png")
                    s.setPixmap(pxm.scaled(8, 8, QtCore.Qt.KeepAspectRatio))

                n = QtWidgets.QLabel()
                n.setText(j["host_name"])

                l.addWidget(s, 0, QtCore.Qt.AlignCenter)
                l.addWidget(n, 0, QtCore.Qt.AlignCenter)

                g.setLayout(l)

                self.job_list.setCellWidget(row, 2, g)

            if "price" in j:
                self.job_list.setItem(row, 3, QtWidgets.QTableWidgetItem("$NT %s" % j['price']))
            if "status" in j:

                if args is not None and args["action"] == "job_status" and str(args["data"]["job_id"]) == str(j["id"]):
                    j["status"] = args["data"]["status"]

                status = j["status"]

                self.job_list.setItem(row, 4, QtWidgets.QTableWidgetItem(status))

                group = QtWidgets.QWidget()
                l = QtWidgets.QHBoxLayout()

                if status == 'completed':
                    dl = QtWidgets.QPushButton()
                    dl.setIcon(QIcon("./src/gui/images/medium/download.png"))
                    dl.clicked.connect(lambda state, x=j['id']: self.download_report(x))
                    dl.setFixedSize(16, 16)
                    dl.setToolTip("Download report")
                    dl.setFlat(True)
                    l.addWidget(dl, 0, QtCore.Qt.AlignLeft)

                elif status == 'pending' or status == 'running':
                    stop = QtWidgets.QPushButton()
                    stop.setIcon(QIcon("./src/gui/images/medium/stop.png"))
                    stop.clicked.connect(lambda state, x=j['id']: self.stop_job(x))
                    stop.setFixedSize(16, 16)
                    stop.setToolTip("Stop job")
                    stop.setFlat(True)
                    l.addWidget(stop, 0, QtCore.Qt.AlignLeft)
                    pass

                elif status == 'stopped' or status == 'failed':

                    start = QtWidgets.QPushButton()
                    start.setIcon(QIcon("./src/gui/images/medium/start.png"))
                    start.setFixedSize(16, 16)
                    start.setFlat(True)
                    start.setIconSize(QSize(16, 16))
                    start.setToolTip("Start job")
                    start.clicked.connect(lambda state, x=j['id']: self.start_job(x))

                    l.addWidget(start, 0, QtCore.Qt.AlignLeft)

                    h = QtWidgets.QPushButton()
                    h.setFixedSize(16, 16)
                    h.setFlat(True)
                    h.setIconSize(QSize(16, 16))
                    h.setIcon(QIcon("./src/gui/images/medium/reselecthost.png"))
                    h.setToolTip("Reselect host")

                    l.addWidget(h, 0, QtCore.Qt.AlignLeft)

                    select_box = QtWidgets.QComboBox()
                    select_box.setFixedSize(QSize(70, 30))
                    select_box.setToolTip("Please Select Host")
                    select_box.activated.connect(lambda state, x=select_box, y=j['id']: self.reassign_host(x, y))
                    l.addWidget(select_box, 0, QtCore.Qt.AlignLeft)
                    select_box.hide()

                    h.clicked.connect(lambda state, x=j['software_id'], y=select_box: self.reselect_host(x, y))
                    pass

                group.setLayout(l)
                self.job_list.setCellWidget(row, 5, group)

            row += 1

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
            # self.job['run_file'] = (pycurl.FORM_BUFFER, os.path.basename(fileName), pycurl.FORM_BUFFERPTR, open(fileName, 'rb'), pycurl.FORM_CONTENTTYPE, content_type)
            self.job['run_file'] = fileName
            self.refresh()
            self.set_step(3)
            self.job_id = None

    def browse_files(self):
        self.job['other_files'] = []
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
                # self.job['other_files[%d]' % k] = (pycurl.FORM_BUFFER, os.path.basename(file), pycurl.FORM_BUFFERPTR, open(file, 'rb'), pycurl.FORM_CONTENTTYPE, content_type)
                # self.job['other_files[%d]' % k] = file
                self.job['other_files'].append(file)
                k += 1

        self.job_id = None

    def submit_job(self):

        if "software_id" not in self.job:
            self.log.info("Please select software", self.console, True)
            return

        '''if "run_file" not in self.job:
            self.log.info("Please select run file", self.console, True)
            return'''

        if "host_id" not in self.job or self.job['host_id'] == 0:
            self.log.info("Please select host", self.console, True)
            return

        self.is_cancel_upload = False

        if self.current_step == 4:
            self.set_step(5)
            self.log.info("Creating job", self.console)

            self.current_job = self.app.api.upload("/job/create", {
                "token": self.app.token,
                "host_id": str(self.job['host_id']),
                "software_id": str(self.job['software_id']),
                "run_file": os.path.basename(self.job['run_file'])
            })

            if self.current_job:

                self.log.info("Uploading file", self.console)

                file = ZipFile(self.app.home_dir + "/.tmp/%s.zip" % self.current_job['uid'], "w")
                file.write(self.job['run_file'], os.path.basename(self.job['run_file']))

                for other_file in self.job['other_files']:
                    file.write(other_file, os.path.basename(other_file))

                file.close()

                threading.Thread(target=self.app.api.curl_upload, args=(
                    "/job/%s/upload_file" % self.current_job['id'], file, self.progress, self.read_function)).start()

                self.timer.timeout.connect(self.run_queue)
                self.timer.start(50)

        pass

    def run_queue(self):

        if not self.callback_queue.empty():
            try:
                callback = self.callback_queue.get(False)
                callback()
            except queue.Empty:
                pass

    def read_function(self, file, size):
        while not self.is_cancel_upload:
            return file.read(size)

        return pycurl.READFUNC_ABORT

    def cancel_upload(self):
        if not self.is_cancel_upload:
            self.is_cancel_upload = True
            self.log.info("Upload canceled", self.console)
            if self.current_job:
                self.app.api.delete("/job/%s/item" % self.current_job['id'])
            self.clear_form()

    '''Pycurl Monitor'''

    def job_submitted(self, percent):

        rate = round(percent, ndigits=2)  # Convert the completed fraction to percentage
        completed = int(rate)
        self.upload_bar.setValue(completed)

        if percent == 100:
            self.log.info("File successfully transferred", self.console)
            self.log.info("Job submitted", self.console, True)

            # Todo Send event to SH
            pusherServer.trigger(job_channel, self.current_job["sh_token"] + ".job_assignments", self.current_job)

            self.clear_form()
            self.set_step(6)
            self.callback_queue.task_done()
            self.timer.stop()
            self.get_job_list()

    def progress(self, total_to_download, total_downloaded, total_to_upload, total_uploaded):
        if total_to_upload:
            percent_completed = float(total_uploaded) / total_to_upload  # You are calculating amount uploaded
            percent = percent_completed * 100
            # How the f.. can i send signal to main thread now?
            self.callback_queue.put(lambda: self.job_submitted(percent))

    '''MultipartEncoderMonitor'''

    def monitor(self, monitor):
        percent = round((monitor.bytes_read / monitor.len) * 100)
        self.upload_bar.setValue(percent)
        if percent == 100:
            self.log.info("File successfully transferred", self.console)
            self.set_step(6)

        pass

    def clear_software(self):
        self.software.clear()
        self.software.addItem("Select Software", 0)

    def clear_host(self):
        self.host.clear()
        self.host.addItem("Select Hosts", 0)

    def clear_form(self):

        Helper.clear_folder(self.app.home_dir + "/.tmp/")

        with self.callback_queue.mutex:
            self.callback_queue.queue.clear()

        self.upload_bar.setValue(0)

        self.job = {}

        # clear host
        self.clear_host()

        # clear files
        self.run_file.clear()

        # clear other files
        self.other_files.clear()

        self.get_software_list()

    def start_job(self, job_id):
        print("start job id: %s" % job_id)
        r = self.app.api.post("/job/%s/start" % job_id)
        if r:
            self.log.info("Job started", self.console)
            pusherServer.trigger(job_channel, r["sh_token"] + ".job_assignments", r)

    def stop_job(self, job_id):
        print("stop job id: %s" % job_id)
        r = self.app.api.post("/job/%s/stop" % job_id)
        if r:
            print("Job stopped", r)
            pusherServer.trigger(job_channel, r["sh_token"] + ".job_stop", r)
            self.log.info("Job stopped", self.console)
            self.get_job_list()
        pass

    def download_report(self, job_id):

        # job_id = self.get_selected_job_id(job_id)

        # job_id = self.job_list.item(row, 0)
        # print("Selected Job ID %s" % job_id)
        self.log.info("Downloading job report...", self.console)
        j = self.app.api.get("/job/%s/download_report" % job_id)

        if j:
            report = download(j['download_url'])
            f = re.findall(r"(\w+).zip$", j['file_url'])

            path = self.app.home_dir + "/reports/" + f[0]
            file_name = path + '.zip'
            open(file_name, "wb").write(report)
            self.log.info("Report file has been saved at %s" % file_name, self.console, True)
            self.set_step(9)

    def reselect_host(self, software_id, select_box):
        host = self.app.api.get("/software/%s/verified-hosts" % software_id)
        if host:
            select_box.clear()
            for h in host:
                select_box.addItem("$NT%s: %s" % (h['price'], h['host_info']), h['id'])
            select_box.showPopup()
        pass

    def reassign_host(self, select_box, job_id):
        new_host_id = select_box.itemData(select_box.currentIndex())
        job = self.app.api.put("/job/%s/item" % job_id, {"host_id": new_host_id})
        if job:
            # Todo Send event to SH
            pusherServer.trigger(job_channel, job["sh_token"] + ".job_assignments", job)
            self.get_job_list()

    def logout(self):
        pusherClient.unsubscribe(job_channel)
        self.app.logout()
