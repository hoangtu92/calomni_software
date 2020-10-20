import os, platform
from os.path import dirname, abspath
from shutil import make_archive
from zipfile import ZipFile

from magic import Magic
from src.api.Api import download
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QGridLayout, QPushButton, QLineEdit, QLabel

from src.classes.Log import Log
from src.classes.Software import Software
import re
from src.classes.Alert import Alert


class ShScreen(QWidget):
    app = None
    current_host = None
    items = 0
    cols = 4
    log = None

    def __init__(self, app):
        self.app = app
        QWidget.__init__(self)

        uic.loadUi(dirname(dirname(abspath(__file__))) + "/gui/sh_screen.ui", self)
        cp = QDesktopWidget().availableGeometry().center()
        qr = self.frameGeometry()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.mime = Magic(mime=True)

        self.host_active = True

        # self.software_list = self.findChild(QGridLayout, "software_list")
        self.content = self.findChild(QWidget, "content")
        self.software_list = QGridLayout()
        self.content.setLayout(self.software_list)

        self.filter_buttons = {
            "A": self.findChild(QPushButton, "A"),
            "B": self.findChild(QPushButton, "B"),
            "C": self.findChild(QPushButton, "C"),
            "D": self.findChild(QPushButton, "D"),
            "E": self.findChild(QPushButton, "E"),
            "F": self.findChild(QPushButton, "F"),
            "G": self.findChild(QPushButton, "G"),
            "H": self.findChild(QPushButton, "H"),
            "I": self.findChild(QPushButton, "I"),
            "J": self.findChild(QPushButton, "J"),
            "K": self.findChild(QPushButton, "K"),
            "L": self.findChild(QPushButton, "L"),
            "M": self.findChild(QPushButton, "M"),
            "N": self.findChild(QPushButton, "N"),
            "O": self.findChild(QPushButton, "O"),
            "P": self.findChild(QPushButton, "P"),
            "Q": self.findChild(QPushButton, "Q"),
            "R": self.findChild(QPushButton, "R"),
            "S": self.findChild(QPushButton, "S"),
            "T": self.findChild(QPushButton, "T"),
            "U": self.findChild(QPushButton, "U"),
            "V": self.findChild(QPushButton, "V"),
            "W": self.findChild(QPushButton, "W"),
            "X": self.findChild(QPushButton, "X"),
            "Y": self.findChild(QPushButton, "Y"),
            "Z": self.findChild(QPushButton, "Z"),
        }

        self.status = self.findChild(QLabel, "status")
        self.online_offline_btn = self.findChild(QPushButton, "online_offline_btn")
        self.bottom = self.findChild(QWidget, "bottom")

        self.filter_buttons["A"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["A"].text()))
        self.filter_buttons["B"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["B"].text()))
        self.filter_buttons["C"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["C"].text()))
        self.filter_buttons["D"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["D"].text()))
        self.filter_buttons["E"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["E"].text()))
        self.filter_buttons["F"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["F"].text()))
        self.filter_buttons["G"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["G"].text()))
        self.filter_buttons["H"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["H"].text()))
        self.filter_buttons["I"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["I"].text()))
        self.filter_buttons["J"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["J"].text()))
        self.filter_buttons["K"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["K"].text()))
        self.filter_buttons["L"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["L"].text()))
        self.filter_buttons["M"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["M"].text()))
        self.filter_buttons["N"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["N"].text()))
        self.filter_buttons["O"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["O"].text()))
        self.filter_buttons["P"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["P"].text()))
        self.filter_buttons["Q"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["Q"].text()))
        self.filter_buttons["R"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["R"].text()))
        self.filter_buttons["S"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["S"].text()))
        self.filter_buttons["T"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["T"].text()))
        self.filter_buttons["U"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["U"].text()))
        self.filter_buttons["V"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["V"].text()))
        self.filter_buttons["W"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["W"].text()))
        self.filter_buttons["X"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["X"].text()))
        self.filter_buttons["Y"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["Y"].text()))
        self.filter_buttons["Z"].clicked.connect(lambda: self.get_software_list(self.filter_buttons["Z"].text()))

        self.searchField = self.findChild(QLineEdit, "search")
        self.searchField.returnPressed.connect(lambda: self.get_software_list(None, self.searchField.text()))

        self.save_check_btn = self.findChild(QPushButton, "save_check_btn")
        self.save_btn = self.findChild(QPushButton, "save_btn")
        self.online_offline_btn = self.findChild(QPushButton, "online_offline_btn")
        self.reset_filter_btn = self.findChild(QPushButton, "reset_filter")

        self.save_btn.clicked.connect(self.save)
        self.save_check_btn.clicked.connect(self.save_and_check)
        self.online_offline_btn.clicked.connect(self.toggle_online_offline)
        self.reset_filter_btn.clicked.connect(lambda: self.get_software_list(None, None))

        self.cols = round(self.width() / 200)

        self.software_list.setColumnStretch(self.cols + 1, 1)


    def append_software(self, obj):
        # the next free position depends on the number of added items
        row = self.items / self.cols
        col = self.items % self.cols
        # add the button to the next free position
        self.software_list.addWidget(obj, row, col)
        # update the number of items
        self.items = self.software_list.count()

    def layout_delete_items(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    self.layout_delete_items(item.layout())

    def clear_software_list(self):

        for i in range(self.software_list.count()):
            s = self.software_list.takeAt(0)
            if s.widget is not None:
                s.widget().setParent(None)

        # self.software_list = QGridLayout()
        # self.content.setLayout(self.software_list)

    def get_software_list(self, keyword=None, search=None):

        params = {"keyword": "", "search": ""}

        if keyword is not None:
            params["keyword"] = keyword

        if search is not None:
            params["search"] = search

        self.clear_software_list()

        soft = self.app.api.get("/software/sh_list", params)

        if soft:

            for s in soft:
                # print(s)
                sw = Software(self, s)
                self.append_software(sw)

        self.software_list.setRowStretch(self.items / self.cols + 1, 1)

    def get_host_info(self):
        r = self.app.api.get("/host/item/%s" % self.app.token)
        if not r:
            r = self.registering_host()
        else:
            if r['status'] == 'active':
                self.bottom.setStyleSheet("background: rgba(123, 255, 56, 186);")
                self.status.setText("Status: Active")
                self.host_active = True
            else:
                self.host_active = False
                self.bottom.setStyleSheet("background:red;")
                self.status.setText("Status: Inactive")

        return r

    def registering_host(self):
        hostnamectl = os.popen("hostnamectl").read()
        hostname = re.findall(r"Operating System: (.+)", hostnamectl)

        cpu_name = os.popen("cat /proc/cpuinfo | grep 'model name' | uniq").read()
        cpu_name = re.findall(r"model name\s+:\s+(.+)", cpu_name)

        cpu_core = os.popen("cat /proc/cpuinfo | grep processor | wc -l").read()
        cpu_core = re.findall(r"\d+", cpu_core)

        cpu_freq = os.popen("cat /proc/cpuinfo | grep 'cpu MHz' | uniq").read()
        cpu_freq = re.findall(r"cpu MHz\s+:\s+(.+)", cpu_freq)

        mem_total = os.popen("cat /proc/meminfo | grep MemTotal").read()
        mem_total = re.findall(r"MemTotal:\s+(.+) kB", mem_total)

        mem_free = os.popen("cat /proc/meminfo | grep MemFree").read()
        mem_free = re.findall(r"MemFree:\s+(.+) kB", mem_free)

        storage = os.popen("df -T /opt/ | grep dev").read()
        storage = re.findall(r"([\w\/]+)\s+([\w]+)\s+([\d]+)\s+([\d]+)\s+([\d]+)\s+([\w\,\.%]+)", storage)

        storage_total = int(storage[0][2])
        storage_free = int(storage[0][4])

        host_info = {
            "token": self.app.token,
            "name": "%s" % (platform.platform()),
            "os": hostname[0],
            "cpu_freq": cpu_freq[0],
            "info": platform.platform(),
            "mem_total": int(mem_total[0]),
            "mem_free": int(mem_free[0]),
            "cpu_name": cpu_name[0],
            "cpu_cores": int(cpu_core[0]),
            "storage_total": storage_total,
            "storage_free": storage_free,
            "mac": self.app.mac
        }

        r = self.app.api.post("/host/create", host_info)

        return r
        pass

    def initializing(self):
        self.log = Log(self.app)
        self.get_host_info()
        self.get_software_list()
        self.fetch_jobs()
        pass

    def save(self, idx=None):
        if idx is None:
            idx = 0

        if idx == self.software_list.count() - 1:
            Alert("Successfully saved!")
            return

        software = self.software_list.itemAt(idx).widget()
        # if software.checked.isChecked():
        software.save()

        idx += 1

        self.save(idx)

    def save_and_check(self, idx=None):
        if idx is None:
            idx = 0

        if idx == self.software_list.count():
            Alert("Successfully saved!")
            return

        software = self.software_list.itemAt(idx).widget()
        if software.checked.isChecked():
            software.test()
            software.save()

        idx += 1
        self.save_and_check(idx)

        pass

    def toggle_online_offline(self):
        if self.host_active:
            status = 'inactive'
            self.bottom.setStyleSheet("background:red;")
            self.status.setText("Status: Inactive")
            self.host_active = False
        else:
            status = 'active'
            self.bottom.setStyleSheet("background: rgba(123, 255, 56, 186);")
            self.status.setText("Status: Active")
            self.host_active = True

        self.app.api.post("/host/item/%s" % self.app.token, {"status" : status})

        pass

    def update_task(self, job_id, status, file_name = None):

        fields = {
            'status': status
        }
        if file_name is not None:
            fields['data'] = (os.path.basename(file_name), open(file_name, 'rb'), self.mime.from_file(file_name))

        r = self.app.api.upload("/job/%s/update_task" % job_id, fields)
        self.log.debug(r)

    def fetch_jobs(self):
        QtCore.QTimer.singleShot(5000, self.fetch_jobs)

        if not self.host_active:
            return

        job = self.app.api.get("/job/assignments", {"token": self.app.token})
        if job:
            for j in job:
                # print(j)
                # Save all files to environment folder
                f = re.findall(r"(\w+).zip$", j['file_url'])

                path = self.app.home_dir + "/environment/" + f[0]
                file_name = path + '.zip'

                # Begin the task
                self.update_task(j['job_id'], "running")

                # Save file
                self.log.info("Save job file to: " + file_name)
                job_file = download(j['file_url'])
                open(file_name, "wb").write(job_file)

                # Extract file
                with ZipFile(file_name, 'r') as zip_ref:
                    zip_ref.extractall(path)
                    os.popen("chmod +x " + path + "/" + j['run_file']).read()
                    os.remove(file_name)

                    command = "cd %s; %s" % (path, j['command'])
                    result = os.popen(command).read()
                    self.log.debug(result)

                    make_archive(path, 'zip', path)

                    self.update_task(j['job_id'], 'completed', file_name)

        pass

