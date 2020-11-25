from pathlib import Path


class Config:

    home = str(Path.home())
    home_dir = home + "/calomni_software"

    @staticmethod
    def load_token():
        p = open(Config.home_dir + "/.config/token.txt", "r")
        token = p.readline()
        p.close()
        return token

    @staticmethod
    def save_token(token):
        p = open(Config.home_dir + "/.config/token.txt", "w")
        p.write(token)
        p.close()
