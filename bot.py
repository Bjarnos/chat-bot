import requests
import dotenv, os
import time
import re

dotenv.load_dotenv()

login_url = "https://chat.jonazwetsloot.nl/login"
actionlogin_url = "https://chat.jonazwetsloot.nl/actionlogin"
send_message_url = "https://chat.jonazwetsloot.nl/api/v1/message"

logindata = {
    "user": os.environ.get('user'),
    "pass": os.environ.get('pass'),
    "redirect": ""
}

session = requests.Session()

headers = { 
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Host": "chat.jonazwetsloot.nl",
    "Origin": "https://chat.jonazwetsloot.nl",
    "Referer": "https://chat.jonazwetsloot.nl/login",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Content-Type": "application/x-www-form-urlencoded",
}

stored_phpsessid = None
token = None

# API
def send_message(message):
    data = {
        "message": message,
        "attachments": "",
        "name": os.environ.get('user'),
        "key": "abc"
    }

    response = session.post(send_message_url, json=data, headers=headers)
    
    print(f"Response Status Code (Send Message): {response.status_code}", flush=True)
    print(f"Response JSON (Send Message): {response.json()}", flush=True)

# Log in
def get_php_session():
    global stored_phpsessid

    if stored_phpsessid:
        print("Reusing stored PHPSESSID:", stored_phpsessid, flush=True)
        return stored_phpsessid

    response = session.get(login_url, headers=headers)

    print(f"Response Status Code (Login): {response.status_code}", flush=True)

    if 'PHPSESSID' in response.cookies:
        stored_phpsessid = response.cookies['PHPSESSID']
        print(f"PHPSESSID from /login cookies: {stored_phpsessid}", flush=True)
        return stored_phpsessid
    else:
        print("PHPSESSID not found in /login response cookies.", flush=True)
        return None

def login(phpsessid):
    headers["Cookie"] = f"PHPSESSID={phpsessid}"

    cookies = {
        "PHPSESSID": phpsessid
    }

    response = session.post(actionlogin_url, data=logindata, headers=headers, cookies=cookies)
    
    print(f"Response Status Code (ActionLogin): {response.status_code}", flush=True)
    return response.status_code == 200 

login(get_php_session())

send_message("Hello, this is a test message!")
