import requests
import json
from datetime import datetime,timedelta
from core.config import AiKey

proxies = {
    'http': '127.0.0.1:1080',
    'https': '127.0.0.1:1081'
}

def send_ai(messages):
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer '+AiKey
    }
    body = {
        "model": "gpt-3.5-turbo",
        "messages": messages
    }
    r = requests.post(url=url, headers=headers, data=json.dumps(body),proxies=proxies)
    resp_text = r.json()['choices'][0]['message']['content']
    return resp_text

def check_price():
    now = datetime.now()
    before_day_ago = now - timedelta(days=99)
    now_date_str = now.strftime("%Y-%m-%d")
    before_day_str = before_day_ago.strftime("%Y-%m-%d")

    url = f'https://api.openai.com/v1/dashboard/billing/usage?start_date={before_day_str}&end_date={now_date_str}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer '+AiKey
    }
    r = requests.get(url=url, headers=headers)
    total_usage = r.json()['total_usage']

    url1 = 'https://api.openai.com/dashboard/billing/subscription'
    r1 = requests.get(url=url1, headers=headers)
    hard_limit_usd = r1.json()['hard_limit_usd']



    return hard_limit_usd,float(total_usage)/100
