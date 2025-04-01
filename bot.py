import requests
import dotenv, os
import time
import re

dotenv.load_dotenv()

login_url = "https://chat.jonazwetsloot.nl/actionlogin"
logindata = {
    "user": os.environ.get('user'),
    "pass": os.environ.get('pass'),
    "redirect": ""
}

session = requests.Session()

def login():
    response = session.post(login_url, data=logindata)
    if 'Set-Cookie' in response.headers:
        raw_cookie = response.headers['Set-Cookie']
        print("Set-Cookie:", raw_cookie)

        # Extract PHPSESSID using regex
        match = re.search(r'PHPSESSID=([^;]+)', raw_cookie)
        if match:
            phpsessid = match.group(1)
            formatted_cookie = f"PHPSESSID={phpsessid}; cookies=true"
            print("Formatted Cookie:", formatted_cookie)
            return formatted_cookie
        else:
            print("PHPSESSID not found in Set-Cookie header.")
            return None
    else:
        print("No Set-Cookie header found.")
        return None

def extract_expiry(cookie):
    parts = cookie.split("; ")
    for part in parts:
        if part.lower().startswith("expires="):
            expiry_str = part.split("=", 1)[1]
            expiry_time = time.mktime(time.strptime(expiry_str, "%a, %d %b %Y %H:%M:%S GMT"))
            return expiry_time
    return None

while True:
    cookie = login()
    if cookie:
        expiry_time = extract_expiry(cookie)
        if expiry_time:
            wait_time = expiry_time - time.time()
            print(f"Cookie expires in {int(wait_time)} seconds. Sleeping...")
            if wait_time > 0:
                time.sleep(wait_time)
        else:
            print("Session cookie detected, re-authenticating in 1 hour.")
            time.sleep(3600)
    else:
        print("Failed to retrieve cookie. Retrying in 60 seconds.")
        time.sleep(60)
