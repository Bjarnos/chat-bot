import requests
import dotenv, os
import re
import time
import threading
from bs4 import BeautifulSoup

dotenv.load_dotenv()

session = requests.Session()

login_url = "https://chat.jonazwetsloot.nl/login"
actionlogin_url = "https://chat.jonazwetsloot.nl/actionlogin"
timeline_url = "https://chat.jonazwetsloot.nl/timeline"
send_message_url = "https://chat.jonazwetsloot.nl/api/v1/message"

headers = { 
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8,application/json,text/plain,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Host": "chat.jonazwetsloot.nl",
    "Origin": "https://chat.jonazwetsloot.nl",
    "Referer": "https://chat.jonazwetsloot.nl/login",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Content-Type": "application/x-www-form-urlencoded",
}

message_cache = {}

# Absolute Core
def convert_to_seconds(time_text):
    number_map = {
        'second': 1,
        'minute': 60,
        'hour': 3600,
        'day': 86400,
        'month': 2592000,
        'year': 31536000,
    }
    
    match = re.match(r'(\d+)\s*(second|minute|hour|day|month|year)', time_text)
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        return num * number_map[unit]

    return 0

def extract_messages(html):
    soup = BeautifulSoup(html, 'html.parser')
    messages = []
    for message_div in soup.find_all('div', class_='message'):
        time_element = message_div.find('p', class_='time')
        content_element = message_div.find('div', class_='content')
        user_element = message_div.find('a', class_='username')
        if time_element and content_element:
            time_text = time_element.text.strip()
            content_text = content_element.text.strip()
            user_text = user_element.text.strip()
            time_in_seconds = time.time() - convert_to_seconds(time_text)
            messages.append({
                "time": time_in_seconds,
                "text": content_text,
                "sender": user_text
            })
    return messages

class FunctionBinder:
    def __init__(self):
        self.functions = []
        self.is_checking = False
        self.last_checked_time = time.time()

    def bind(self, func):
        self.functions.append(func)

    def _run_bound_functions(self, message):
        for func in self.functions:
            func(message)

    def start_checking(self):
        if not self.is_checking:
            self.is_checking = True
            threading.Thread(target=self._check_periodically).start()

    def _check_periodically(self):
        while self.is_checking:
            print("Checking...")

            try:
                response = requests.get(timeline_url, headers=headers)
                if response.status_code == 200:
                    messages = extract_messages(response.text)
                    if messages:
                        if self.last_checked_time is None:
                            self.last_checked_time = messages[0].time
                        else:
                            for message in reversed(messages):
                                self._remove_expired_messages()
                                
                                cache_key = content[:10]
                                if cache_key not in message_cache:
                                    self._run_bound_functions(message)
                                    message_cache[cache_key] = message.time

                            self.last_checked_time = messages[0].time
            except Exception as e:
                print(f"Error checking for new posts: {e}")
            time.sleep(10)

    def stop_checking(self):
        self.is_checking = False

    def _remove_expired_messages(self):
        """ Remove messages from cache older than 10 minutes (600 seconds). """
        current_time = time.time()
        keys_to_remove = [key for key, timestamp in message_cache.items() if current_time - timestamp > 600]
        for key in keys_to_remove:
            del message_cache[key]

# Core functions
def get_php_session():
    """ Get initial PHPSESSID from the login page """
    response = session.get(login_url, headers=headers)
    print(f"Login Page Response: {response.status_code}")

def login(username, password):
    """ Perform the actual login request """
    logindata = {
        "user": username,
        "pass": password,
        "redirect": ""
    }

    response = session.post(actionlogin_url, data=logindata, headers=headers)
    print(f"Response Status Code (ActionLogin): {response.status_code}")

    return response.status_code == 200

def get_key():
    """ Extracts the key needed for sending messages """
    response = session.get(timeline_url, headers=headers)
    match = re.search(r'<input[^>]+name="key"[^>]+value="([^"]+)"', response.text)
    if match:
        return match.group(1)
    return None

# API
def send_message(message):
    """ Sends a message using the chat API """
    key = get_key()
    if not key:
        print("Failed to retrieve key.")
        return

    data = {
        "message": message,
        "attachments": "",
        "name": os.environ.get('user'),
        "key": key
    }
    response = session.post(send_message_url, data=data, headers=headers)
    print(f"Response Status Code (Send Message): {response.status_code}")

# Example Core
get_php_session()
if login(os.environ.get('user'), os.environ.get('pass')):
    # Example client
    binder = FunctionBinder()

    def ping(message):
        print("Found a message!")
        print("Content text: " + message.text)
        print("Sender: " + message.sender)
    binder.bind(ping)

    binder.start_checking()
    
    send_message("||This message was automatically generated by a selfbot.||")
