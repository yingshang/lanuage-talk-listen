from core.config import AppKey,AppSecret
import requests,json

api_host = "https://api.dingtalk.com"


class DingDing(object):
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json;charset=utf-8"
        }
        self.access_token = self.get_access_token()


    def get_access_token(self):
        url = api_host + "/v1.0/oauth2/accessToken"
        headers = {
            "Host": "api.dingtalk.com",
            "Content-Type": "application/json"
        }
        data = {
            "appKey": AppKey,
            "appSecret": AppSecret
        }
        r = requests.post(url=url, headers=headers, data=json.dumps(data))
        token = r.json()['accessToken']
        return token
