import logging
import os
import shutil
from zipfile import ZipFile

from src.api.Api import download, Api, mime
from src.classes.Config import Config


class Helper:

    @staticmethod
    def clear_folder(folder):
        # folder = self.app.home_dir + "/.tmp/"
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
