import os, pycurl

import magic
import requests
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

from src.classes.Config import Config

mime = magic.Magic(mime=True)

def download(url):
    return requests.get(url, allow_redirects=True).content


# Class which holds a file reference and the read callback
class FileReader:
    def __init__(self, file, callback):
        self.file = file
        self.callback = callback

    def read_callback(self, size):
        return self.callback(self.file, size)

class Api:
    apiUrl = "https://calomni.com/api"
    bearer = Config.load_token()
    user = {}

    def __init__(self, app):
        self.app = app
        self.bearer = Config.load_token()
        pass

    def url(self, endpoint):
        return self.apiUrl + endpoint

    def login_bearer(self):
        self.app.log.info("Login to system")
        user = self.get("/user")
        if user:
            self.app.log.debug("User info: %s" % user)
            self.user = user
            return self.user
        return False

    '''Login to the api'''

    def login(self, email, password):
        self.app.log.info("Login to system")

        try:
            resp = requests.post(self.url("/auth/login"), data={'email': email, 'password': password},
                                 headers={"Accept": "application/json"})

            if resp.status_code == 200 or resp.status_code == 201:
                result = resp.json()
                self.bearer = result['data']['plainTextToken']
                Config.save_token(self.bearer)
                user = self.get("/user")
                if user:
                    self.app.log.debug("User info: %s" % user)
                    self.user = user
                    return True

            elif resp.status_code == 422:
                self.app.log.error("Login incorrect", None, True)

            else:
                self.app.log.error("Error: %s\n%s" % (resp.status_code, resp.reason), None, True,
                                   lambda: self.app.timer.start(5000))

            return False

        except:
            self.app.log.info("Connection error")
            return False

    '''Logout'''

    def logout(self):
        try:
            self.post(self.url("/auth/logout"))
            self.bearer = None
            return True

        except:
            self.app.log.info("Connection error")
            return False

    def back_to_login(self):
        self.app.sh_screen.hide()
        self.app.rh_screen.hide()
        self.app.login_screen.show()

    '''Inspector'''

    def response(self, resp):
        # Success
        if resp.status_code == 200 or resp.status_code == 201:
            result = resp.json()
            if 'status' in result:
                if result['status']:
                    if "message" in result and result["message"]:
                        self.app.log.info(result['message'], None, True)

                    return result['data']
                else:
                    self.show_error(result['message'], self.app.start_timer)
            else:
                self.app.log.debug(result)
                self.show_error("Invalid data received", self.app.start_timer)

        # Bad request
        elif resp.status_code == 400:
            result = resp.json()
            self.show_error(result["message"], self.app.start_timer)

        # Unauthenticated
        elif resp.status_code == 401:
            self.show_error("Session expired! Please login again", self.back_to_login)

        # Everything else
        else:
            self.app.log.debug(resp.json())
            self.show_error("Error: %s\n%s" % (resp.status_code, resp.reason), self.app.start_timer)

        return False

    def show_error(self, msg, callback=None):
        try:
            self.app.timer.stop()
        except:
            pass
        self.app.log.error(msg, None, True, callback)

    '''get request'''

    def get(self, endpoint, params=None):

        if self.bearer is None:
            self.show_error("Session expired! Please login again", self.back_to_login)
            return False

        try:
            resp = requests.get(self.url(endpoint), params=params,
                                headers={"Accept": "application/json", "Authorization": "Bearer " + self.bearer})
            return self.response(resp)

        except:
            self.show_error("Connection error", self.app.start_timer)
            return False

    '''put request'''

    def put(self, endpoint, data=None, files=None):
        if self.bearer is None:
            return False

        try:
            resp = requests.put(self.url(endpoint), data=data,
                                headers={"Accept": "application/json", "Authorization": "Bearer " + self.bearer})

            return self.response(resp)

        except:
            self.show_error("Connection error", self.app.start_timer)
            return False

    '''post request'''

    def post(self, endpoint, data=None, files=None):
        if self.bearer is None:
            return False

        try:
            resp = requests.post(self.url(endpoint), data=data, files=files,
                             headers={"Accept": "application/json", "Authorization": "Bearer " + self.bearer})

            return self.response(resp)

        except:
            self.show_error("Connection error", self.app.start_timer)
            return False

    '''upload'''

    def upload(self, endpoint, data, callback=None):

        if self.bearer is None:
            return False

        m = MultipartEncoder(fields=data)
        if callback is not None:
            m = MultipartEncoderMonitor(m, callback)

        try:
            resp = requests.post(self.url(endpoint), data=m,
                                 headers={"Content-Type": m.content_type, "Accept": "application/json",
                                          "Authorization": "Bearer " + self.bearer})
            return self.response(resp)

        except:
            self.show_error("Connection error", self.app.start_timer)
            return False

    @staticmethod
    def silence_upload(endpoint, data, callback=None, return_value=None):

        if Api.bearer is None:
            return False

        m = MultipartEncoder(fields=data)
        if callback is not None:
            m = MultipartEncoderMonitor(m, callback)

        try:
            resp = requests.post(Api.apiUrl + endpoint, data=m,
                                 headers={"Content-Type": m.content_type, "Accept": "application/json",
                                          "Authorization": "Bearer " + Api.bearer})
            if return_value:
                return_value.value = resp

            return resp
        except:
            print("Failed", endpoint, data)
            return False
        pass

    @staticmethod
    def static_get(endpoint, params=None):
        if Api.bearer is None:
            return False

        try:
            resp = requests.get(Api.apiUrl + endpoint, params=params,
                                headers={"Accept": "application/json", "Authorization": "Bearer " + Api.bearer})

            return resp.json()

        except:
            return False


    '''delete request'''

    def delete(self, endpoint):
        if self.bearer is None:
            return False

        try:
            resp = requests.delete(self.url(endpoint),
                                   headers={"Accept": "application/json", "Authorization": "Bearer " + self.bearer})

            return self.response(resp)

        except:
            self.show_error("Connection error", self.app.start_timer)
            return False

    @staticmethod
    def curl_upload(endpoint, file, progress=None, read_function=None):

        url = Api.apiUrl + endpoint

        # upload = list()

        '''data['other_files'] = ""

        for key in data:
            if key == "run_file" or re.search("other_files", key):
                content_type = mime.from_file(data[key])
                upload.append((key, (pycurl.FORM_FILE, data[key], pycurl.FORM_FILENAME, os.path.basename(data[key]), pycurl.FORM_CONTENTTYPE, content_type )))
            else:
            if key == "run_file":
                upload.append((key, os.path.basename(data[key])))
            else:
                upload.append((key, data[key]))
        '''

        # content_type = mime.from_file(file.filename)
        # upload.append(('file', (pycurl.FORM_FILE, file.filename, pycurl.FORM_FILENAME, os.path.basename(file.filename), pycurl.FORM_CONTENTTYPE, content_type )))

        # print(upload)

        # initialize py curl
        c = pycurl.Curl()

        if read_function:
            c.setopt(pycurl.READFUNCTION, FileReader(open(file.filename, "rb"), read_function).read_callback)

        c.setopt(pycurl.INFILESIZE, os.path.getsize(file.filename))

        c.setopt(pycurl.VERBOSE, 0)
        c.setopt(pycurl.UPLOAD, 1)
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.NOPROGRESS, 0)

        c.setopt(pycurl.HTTPHEADER, [
            "Accept: application/json",
            "Authorization: Bearer " + Api.bearer
        ])

        if progress:
            c.setopt(pycurl.XFERINFOFUNCTION, progress)
            c.setopt(pycurl.PROGRESSFUNCTION, progress)

        c.perform()         # this kicks off the pycurl module with all options set.
        c.close()

        return c
