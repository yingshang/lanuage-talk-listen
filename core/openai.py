import requests
import json
from datetime import datetime, timedelta
from core.config import AiKeyList
import random,time

proxies = {
    'http': '127.0.0.1:1080',
    'https': '127.0.0.1:1081'
}


def send_ai(messages):
    while len(AiKeyList) > 0:
        AiKey = random.choice(AiKeyList)
        url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + AiKey
        }
        body = {
            "model": "gpt-3.5-turbo",
            "messages": messages
        }
        r = requests.post(url=url, headers=headers, data=json.dumps(body))
        resp_text = r.json()
        try:
            content = resp_text['choices'][0]['message']['content']
            return content
        except Exception as e:
            if "exceeded your current quota" in str(resp_text):
                AiKeyList.remove(AiKey)
            elif "Incorrect API key provided:" in str(resp_text):
                AiKeyList.remove(AiKey)
            else:
                time.sleep(5)
        else:
            break
    return


def check_price():
    now = datetime.now()
    before_day_ago = now - timedelta(days=99)
    now_date_str = now.strftime("%Y-%m-%d")
    before_day_str = before_day_ago.strftime("%Y-%m-%d")
    resp_text = ""
    for AiKey in AiKeyList:
        try:
            url = f'https://api.openai.com/v1/dashboard/billing/usage?start_date={before_day_str}&end_date={now_date_str}'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + AiKey
            }
            r = requests.get(url=url, headers=headers)
            total_usage = r.json()['total_usage']

            url1 = 'https://api.openai.com/dashboard/billing/subscription'
            r1 = requests.get(url=url1, headers=headers)
            hard_limit_usd = r1.json()['hard_limit_usd']/100
            resp_text = resp_text+"Key:{}\n\n授权金额:{}\n\n总共使用:{}\n\n".format(AiKey[-6:-1],hard_limit_usd, total_usage)
        except:
            resp_text = resp_text+"Key:{}无效\n\n".format(AiKey[-6:-1])

    return resp_text
