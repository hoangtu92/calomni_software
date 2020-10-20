import logging
from datetime import datetime

from src.classes.Alert import Alert


class Log:
    def __init__(self, app):
        self.app = app

        file_name = "general.log"

        if 'uid' in self.app.api.user:
            file_name = "%s.log" % self.app.api.user['uid']

        handler = logging.FileHandler("%s/logs/%s" % (self.app.home_dir, file_name))
        handler.setFormatter(logging.Formatter('%(asctime)s: %(levelname)s. %(message)s', '%m/%d/%Y %I:%M:%S %p'))

        self.log = logging.getLogger(file_name)
        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(handler)

    def debug(self, msg, console=None, alert=None):
        self.log.debug(msg)
        self.app_log(msg, console, alert)

    def warning(self, msg, console=None, alert=None):
        self.log.warning(msg)
        self.app_log(msg, console, alert)

    def info(self, msg, console=None, alert=None):
        self.log.info(msg)
        self.app_log(msg, console, alert)

    def error(self, msg, console=None, alert=None):
        self.log.error(msg)
        self.app_log(msg, console, alert)

    def app_log(self, msg, console, alert):
        if alert is not None:
            Alert(msg)
        if console is not None:
            today = datetime.now()
            date = today.strftime("%Y/%m/%d %H:%M:%S")
            console.append("%s %s" % (date, msg))
