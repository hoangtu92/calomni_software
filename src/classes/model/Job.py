class Job:

    def __init__(self, job):
        self.job_id = job['job_id']
        self.user_id = job['user_id']
        self.job_uid = job['job_uid']
        self.users_uid = job['users_uid']
        self.software_id = job['software_id']
        self.status = job['status']
        self.run_file = job['run_file']
        self.command = job['command']
        self.file_url = job['file_url']
        pass

    def __getstate__(self):
        return self.__dict__.copy()
