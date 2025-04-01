import requests
import dotenv, os
import time
import re

dotenv.load_dotenv()

login_url = "https://chat.jonazwetsloot.nl/login"
actionlogin_url = "https://chat.jonazwetsloot.nl/actionlogin"
logindata = {
    "user": os.environ.get('user'),
    "pass": os.environ.get('pass'),
    "redirect": ""
}

session = requests.Session()

headers = { 
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Host": "chat.jonazwetsloot.nl",
    "Priority": "u=0, i",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://chat.jonazwetsloot.nl",
    "Referer": "https://chat.jonazwetsloot.nl/login"
}

stored_phpsessid = None
token = None

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
    #headers["Cookie"] = f"PHPSESSID={phpsessid}"

    #cookies = {
    #    "PHPSESSID": phpsessid
    #}

    response = session.post(actionlogin_url, data=logindata, headers=headers )#cookies=cookies)
    
    print(f"Response Status Code (ActionLogin): {response.status_code}", flush=True)
    print(f"Response Headers (ActionLogin): {response.headers}", flush=True)
    
    print("Response Cookies (ActionLogin):")
    for cookie_name, cookie_value in response.cookies.items():
        print(f"Cookie for /actionlogin: {cookie_name} = {cookie_value}", flush=True)

    if 'PHPSESSID' in response.cookies:
        ttoken = response.cookies['PHPSESSID']
        print(f"PHPSESSID from /actionlogin cookies: {ttoken}", flush=True)
        return ttoken
    else:
        print("PHPSESSID not found in /actionlogin response cookies.", flush=True)
        return None

while True:
    phpsessid = get_php_session()
    if phpsessid:
        token = login(phpsessid)
        if token:
            print("All good!", flush=True)
        else:
            print("Failed to retrieve cookie. Retrying in 60 seconds.", flush=True)
            time.sleep(60)
    else:
        print("Failed to retrieve PHPSESSID. Retrying in 60 seconds.", flush=True)
        time.sleep(60)
