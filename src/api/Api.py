import requests
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor


def download(url):
    return requests.get(url, allow_redirects=True).content


class Api:
    apiUrl = "http://calomni.com/api"
    bearer = None
    user = {}

    def __init__(self, app):
        self.app = app
        self.bearer = None
        pass

    def url(self, endpoint):
        return self.apiUrl + endpoint

    '''Login to the api'''

    def login(self, email, password):
        self.app.log.info("Login to system")

        try:
            resp = requests.post(self.url("/auth/login"), data={'email': email, 'password': password},
                                 headers={"Accept": "application/json"})

            if resp.status_code == 200:
                result = resp.json()
                self.bearer = result['data']['plainTextToken']
                user = self.get("/user")
                if user:
                    self.app.log.debug("User info: %s" % user)
                    self.user = user
                    return True

            if resp.status_code == 422:
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
            if 'status' in result and result['status']:
                return result['data']
            else:
                self.app.log.debug(result)
                self.show_error("Invalid data received", self.app.start_timer)

        # Bad request
        if resp.status_code == 400:
            result = resp.json()
            self.show_error(result["message"], self.app.start_timer)

        # Unauthenticated
        if resp.status_code == 401:
            self.show_error("Session expired! Please login again", self.back_to_login)

        # Everything else
        else:
            self.app.log.debug(resp.json())
            self.show_error("Error: %s\n%s" % (resp.status_code, resp.reason), self.app.start_timer)

        return False

    def show_error(self, msg, callback=None):
        try:
            self.app.timer.stop()
            self.app.job_info_timer.stop()
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
