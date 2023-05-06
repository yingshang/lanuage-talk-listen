#! /usr/bin/env python3.8
import os, json
import logging
import requests
from datetime import datetime
from requests_toolbelt import MultipartEncoder

# const
TENANT_ACCESS_TOKEN_URI = "/open-apis/auth/v3/tenant_access_token/internal"
MESSAGE_URI = "/open-apis/im/v1/messages"


class MessageApiClient(object):
    def __init__(self, app_id, app_secret, lark_host):
        self._app_id = app_id
        self._app_secret = app_secret
        self._lark_host = lark_host
        self._tenant_access_token = ""

    @property
    def tenant_access_token(self):
        return self._tenant_access_token

    def send_text_with_open_id(self, open_id, content):
        self.send("open_id", open_id, "text", content)

    def download_audio(self, message_id, file_key,filepath):
        self._authorize_tenant_access_token()
        url = "{}{}/{}/resources/{}?type=file".format(
            self._lark_host, MESSAGE_URI, message_id, file_key
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        resp = requests.get(url=url, headers=headers)
        with open(filepath, 'wb') as f:
            f.write(resp.content)
        return filepath

    def get_message(self, message_id):
        self._authorize_tenant_access_token()
        url = "{}{}/{}".format(
            self._lark_host, MESSAGE_URI, message_id
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        resp = requests.get(url=url, headers=headers)
        try:
            root_id = resp.json()['data']['items'][0]['root_id']
        except:
            root_id = None

        try:
            parent_id = resp.json()['data']['items'][0]['parent_id']
        except:
            parent_id = None

        return root_id,parent_id

    def upload_audio_file(self, filepath, duration_ms):
        self._authorize_tenant_access_token()
        filename = filepath.split("/")[-1]
        # 请注意使用时替换文件path和Authorization
        url = "https://open.feishu.cn/open-apis/im/v1/files"
        form = {
            'file_type': 'opus',
            'file_name': filename,
            'duration': str(duration_ms),
            'file': (filename, open(filepath, 'rb'), 'text/plain')
        }
        multi_form = MultipartEncoder(form)
        headers = {
            "Authorization": "Bearer " + self.tenant_access_token
        }

        headers['Content-Type'] = multi_form.content_type
        response = requests.request("POST", url, headers=headers, data=multi_form)
        file_key = response.json()['data']['file_key']
        return file_key

    def upload_stream_file(self, filepath):
        self._authorize_tenant_access_token()
        if "\\" in filepath:
            filename = filepath.split("\\")[-1]
        else:
            filename = filepath.split("/")[-1]
        # 请注意使用时替换文件path和Authorization
        url = "https://open.feishu.cn/open-apis/im/v1/files"
        form = {
            'file_type': 'stream',
            'file_name': filename.replace(".opus",'.mp3'),
            'file': (filename, open(filepath, 'rb'), 'text/plain')
        }
        multi_form = MultipartEncoder(form)
        headers = {
            "Authorization": "Bearer " + self.tenant_access_token
        }

        headers['Content-Type'] = multi_form.content_type
        response = requests.request("POST", url, headers=headers, data=multi_form)
        file_key = response.json()['data']['file_key']
        return file_key

    # https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/im-v1/message/create_json
    def reply_send(self, message_id, content, msg_type):
        self._authorize_tenant_access_token()
        url = "{}{}/{}/reply".format(
            self._lark_host, MESSAGE_URI, message_id
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        if msg_type == 'text':
            c = json.dumps({"text": content})
        elif msg_type == 'audio':
            c = json.dumps({"file_key": content})
        elif msg_type == 'post':
            c = json.dumps({"zh_cn": content})

        elif msg_type == 'file':
            c = json.dumps({"file_key": content})

        req_body = {
            "content": c,
            "msg_type": msg_type,
        }
        resp = requests.post(url=url, headers=headers, json=req_body).json()['data']
        msgcontent = json.loads(resp['body']['content'])
        message_id = resp['message_id']
        msg_type = resp['msg_type']
        parent_id = resp['parent_id']
        root_id = resp['root_id']
        if msg_type == 'text':
            content = msgcontent['text']
        elif msg_type =='audio':
            content = msgcontent['file_key']
        return message_id,parent_id,root_id,content




    def _authorize_tenant_access_token(self):
        # get tenant_access_token and set, implemented based on Feishu open api capability. doc link: https://open.feishu.cn/document/ukTMukTMukTM/ukDNz4SO0MjL5QzM/auth-v3/auth/tenant_access_token_internal
        url = "{}{}".format(self._lark_host, TENANT_ACCESS_TOKEN_URI)
        req_body = {"app_id": self._app_id, "app_secret": self._app_secret}
        response = requests.post(url, req_body)
        MessageApiClient._check_error_response(response)
        self._tenant_access_token = response.json().get("tenant_access_token")

    @staticmethod
    def _check_error_response(resp):
        # check if the response contains error information
        if resp.status_code != 200:
            resp.raise_for_status()
        response_dict = resp.json()
        code = response_dict.get("code", -1)
        if code != 0:
            logging.error(response_dict)
            raise LarkException(code=code, msg=response_dict.get("msg"))


class LarkException(Exception):
    def __init__(self, code=0, msg=None):
        self.code = code
        self.msg = msg

    def __str__(self) -> str:
        return "{}:{}".format(self.code, self.msg)

    __repr__ = __str__
