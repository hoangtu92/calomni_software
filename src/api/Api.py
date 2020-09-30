import requests

from src.classes.Alert import Alert


class Api:
    apiUrl = "http://calomnic.wwwaz1-ts1.a2hosted.com/api"
    bearer = None
    user = {}

    def __init__(self):
        self.bearer = None
        pass

    def url(self, endpoint):
        return self.apiUrl + endpoint

    '''Login to the api'''
    def login(self, email, password):
        resp = requests.post(self.url("/auth/login"), data={'email': email, 'password': password},
                             headers={"Accept": "application/json"})

        if resp.status_code == 200:
            self.bearer = resp.text
            res = self.get("/user")
            if res['data']:
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
                Alert(result['message'])
                print(result)
                return False
            return result
        else:
            print(resp.content)
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
    def upload(self, endpoint, data=None):

        if self.bearer is None:
            return False

        resp = requests.post(self.url(endpoint), data=data,
                             headers={"Content-Type": data.content_type, "Accept": "application/json", "Authorization": "Bearer " + self.bearer})
        return self.response(resp)

    '''delete request'''
    def delete(self, endpoint):
        if self.bearer is None:
            return False

        resp = requests.delete(self.url(endpoint),
                               headers={"Accept": "application/json", "Authorization": "Bearer " + self.bearer})

        return self.response(resp)
