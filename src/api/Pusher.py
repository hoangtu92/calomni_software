import hashlib
import pusher
import pysher
from getmac import get_mac_address as gma


mac = gma()

pInfo = {
            "app_id": "1181549",
            "key": 'bba0d882a34df077e259',
            "secret": 'af08f19c4a28b27a60dd',
            "cluster": "mt1",
            "host": 'calomni.com',
            "port": 6001
        }

device_token = hashlib.md5(mac.encode("utf-8")).hexdigest()

job_channel = "presence-job_channel"

pusherServer = pusher.Pusher(pInfo["app_id"], pInfo["key"], pInfo["secret"], cluster=pInfo["cluster"], host=pInfo["host"], port=pInfo["port"], ssl=False)

pusherClient = pysher.Pusher(pInfo["key"], cluster=pInfo["cluster"], secure=False, secret=pInfo["secret"], user_data={"user_id": device_token},
                 daemon=True, port=pInfo["port"], reconnect_interval=10, custom_host=pInfo["host"], auto_sub=False)
