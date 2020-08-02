# Original from: https://github.com/Unna000/Hastebin-API
# Edited to run better

import requests
import json

def get_key(data):
    req = requests.post('https://hastebin.com/documents',
                        # headers={},
                        data=data)

    key = json.loads(req.content)
    return key['key']