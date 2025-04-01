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

# Define human-like headers
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"
}

# Store PHPSESSID for reuse
stored_phpsessid = None

def get_php_session():
    global stored_phpsessid

    # If we already have a PHPSESSID, reuse it
    if stored_phpsessid:
        print("Reusing stored PHPSESSID:", stored_phpsessid, flush=True)
        return stored_phpsessid

    # Perform a GET request to /login to receive the PHPSESSID cookie with human-like headers
    response = session.get(login_url, headers=headers)

    print(f"Response Status Code (Login): {response.status_code}", flush=True)
    print(f"Response Headers (Login): {response.headers}", flush=True)
    print(f"Response Cookies (Login): {response.cookies}", flush=True)  # Print the response cookies

    # Extract PHPSESSID from cookies
    if 'PHPSESSID' in response.cookies:
        stored_phpsessid = response.cookies['PHPSESSID']
        print(f"PHPSESSID from /login cookies: {stored_phpsessid}", flush=True)
        return stored_phpsessid
    else:
        print("PHPSESSID not found in /login response cookies.", flush=True)
        return None

def login(phpsessid):
    # Add the PHPSESSID to the cookies header for actionlogin and include human-like headers
    headers["Cookie"] = f"PHPSESSID={phpsessid}"

    response = session.post(actionlogin_url, data=logindata, headers=headers)
    
    print(f"Response Status Code (ActionLogin): {response.status_code}", flush=True)
    print(f"Response Headers (ActionLogin): {response.headers}", flush=True)
    print(f"Response Cookies (ActionLogin): {response.cookies}", flush=True)  # Print the response cookies

    # Check for Set-Cookie header and handle the session
    if 'set-cookie' in response.headers:
        raw_cookie = response.headers['set-cookie']
        print("Set-Cookie:", raw_cookie, flush=True)

        match = re.search(r'PHPSESSID=([^;]+)', raw_cookie)
        if match:
            phpsessid = match.group(1)
            formatted_cookie = f"PHPSESSID={phpsessid}; cookies=true"
            print("Formatted Cookie:", formatted_cookie, flush=True)
            return formatted_cookie
        else:
            print("PHPSESSID not found in Set-Cookie header.", flush=True)
            return None
    else:
        print("No Set-Cookie header found.", flush=True)
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
    # Step 1: Get PHPSESSID by visiting /login with human-like headers
    phpsessid = get_php_session()
    
    if phpsessid:
        # Step 2: Perform login using the PHPSESSID cookie with human-like headers
        cookie = login(phpsessid)
        if cookie:
            expiry_time = extract_expiry(cookie)
            if expiry_time:
                wait_time = expiry_time - time.time()
                print(f"Cookie expires in {int(wait_time)} seconds. Sleeping...", flush=True)
                if wait_time > 0:
                    time.sleep(wait_time)
            else:
                print("Session cookie detected, re-authenticating in 1 hour.", flush=True)
                time.sleep(3600)
        else:
            print("Failed to retrieve cookie. Retrying in 60 seconds.", flush=True)
            time.sleep(60)
    else:
        print("Failed to retrieve PHPSESSID. Retrying in 60 seconds.", flush=True)
        time.sleep(60)
