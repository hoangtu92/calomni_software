class Response:

    status = True
    message = None
    code = None
    data = None

    def __init__(self, status, message, data=None, code=None):
        self.status = status
        self.message = message
        self.data = data
        self.code = code




