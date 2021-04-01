import pusher
import pysher

pInfo = {
            "app_id": "1181549",
            "key": 'bba0d882a34df077e259',
            "secret": 'af08f19c4a28b27a60dd',
            "cluster": "mt1",
            "host": 'calomni.com',
            "port": 6001
        }

pusherServer = pusher.Pusher(pInfo["app_id"], pInfo["key"], pInfo["secret"], cluster=pInfo["cluster"], host=pInfo["host"], port=pInfo["port"], ssl=False)

pusherClient = pysher.Pusher(pInfo["key"], cluster=pInfo["cluster"], secure=False, secret=pInfo["secret"], user_data=None,
                 daemon=True, port=pInfo["port"], reconnect_interval=10, custom_host=pInfo["host"], auto_sub=False)
