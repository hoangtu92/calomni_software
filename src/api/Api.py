import requests
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

def download(url):
    return requests.get(url, allow_redirects=True).content


class Api:
    apiUrl = "http://calomnic.wwwaz1-ts1.a2hosted.com/api"
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
        resp = requests.post(self.url("/auth/login"), data={'email': email, 'password': password},
                             headers={"Accept": "application/json"})

        if resp.status_code == 200:
            self.bearer = resp.text
            res = self.get("/user")
            if res['data']:
                self.app.log.debug("User info: %s" % res['data'])
                self.user = res['data']

    '''Logout'''
    def logout(self):
        self.post(self.url("/auth/logout"))
        self.bearer = None

    '''Inspector'''
    def response(self, resp):
        if resp.content:
            result = resp.json()
            if 'status' in result and not result['status']:
                self.app.log.error(result['message'], None, True)
                self.app.log.debug(result)
                return False
            return result
        else:
            self.app.log.error(resp.content)
        return False

    '''get request'''
    def get(self, endpoint, params=None):

        if self.bearer is None:
            return False

        resp = requests.get(self.url(endpoint), params=params,
                            headers={"Accept": "application/json", "Authorization": "Bearer " + self.bearer})
        return self.response(resp)

    '''put request'''
    def put(self, endpoint, data=None, files=None):
        if self.bearer is None:
            return False

        resp = requests.put(self.url(endpoint), data=data,
                            headers={"Accept": "application/json", "Authorization": "Bearer " + self.bearer})

        return self.response(resp)

    '''post request'''
    def post(self, endpoint, data=None, files=None):
        if self.bearer is None:
            return False

        resp = requests.post(self.url(endpoint), data=data, files=files,
                             headers={"Accept": "application/json", "Authorization": "Bearer " + self.bearer})

        return self.response(resp)

    '''upload'''
    def upload(self, endpoint, data, callback=None):

        if self.bearer is None:
            return False

        m = MultipartEncoder(fields=data)
        if callback is not None:
            m = MultipartEncoderMonitor(m, callback)

        resp = requests.post(self.url(endpoint), data=m,
                             headers={"Content-Type": m.content_type, "Accept": "application/json", "Authorization": "Bearer " + self.bearer})
        return self.response(resp)

    '''delete request'''
    def delete(self, endpoint):
        if self.bearer is None:
            return False

        resp = requests.delete(self.url(endpoint),
                               headers={"Accept": "application/json", "Authorization": "Bearer " + self.bearer})

        return self.response(resp)


