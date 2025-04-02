# Imports
import requests
import dotenv, os
import re
import time
import threading
from bs4 import BeautifulSoup

# Preloads
dotenv.load_dotenv()
session = requests.Session()

# Constants
url = "https://chat.jonazwetsloot.nl"
api_url = f"{url}/api/v1"
login_url = f"{url}/login"
actionlogin_url = f"{url}/actionlogin"
timeline_url = f"{url}/timeline"
send_message_url = f"{api_url}/message"
like_url = f"{api_url}/like"

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

# Variables
message_cache = {}

# API
user = None
def create_post(message=False):
    """ Sends a message """
    if not message:
        return
    
    key = get_key()
    if not key:
        print("Failed to retrieve key.")
        return

    data = {
        "message": message,
        "attachments": "",
        "name": user,
        "key": key
    }
    response = session.post(send_message_url, data=data, headers=headers)
    print(f"Response Status Code (Send Message): {response.status_code}")

def reply(message_id=False, message=False):
    """ Sends a message """
    if not message_id:
        return
    
    if not message:
        return
    
    key = get_key()
    if not key:
        print("Failed to retrieve key.")
        return

    data = {
        "message": message,
        "id": message_id,
        "name": user,
        "key": key
    }
    response = session.post(send_message_url, data=data, headers=headers)
    print(f"Response Status Code (Send Message): {response.status_code}")

def like(message_id=False, value=True):
    """ Likes a message """
    if not message_id:
        return
    
    key = get_key()
    if not key:
        print("Failed to retrieve key.")
        return
    
    data = {
        "id": message_id,
        "like": str(value).lower(),
        "name": user,
        "key": key
    }
    response = session.post(like_url, data=data, headers=headers)
    print(f"Response Status Code (Like Message): {response.status_code}")

# Custom Message class
class Message:
    def __init__(self, time, text, sender, id):
        self.time = time
        self.text = text
        self.sender = sender
        self.id = str(id)

    def __repr__(self):
        if len(self.text) > 30:
            return f"Message(from {self.sender}): {self.text[:30]}..."
        else:
            return f"Message(from {self.sender}): {self.text}"

    def like(self, value=True):
        like(self.id, value)

    def reply(self, message=False):
        reply(self.id, message)
    
    # Return time as formatted string?
    def get_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.time))

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
        
        message_id_element = message_div.find('button', class_='submit inverted message-menu-share-button')
        message_id = message_id_element['data-id'] if message_id_element and 'data-id' in message_id_element.attrs else None
        if time_element and content_element:
            time_text = time_element.text.strip()
            content_text = content_element.text.strip()
            user_text = user_element.text.strip()
            time_in_seconds = time.time() - convert_to_seconds(time_text)
            message = Message(time_in_seconds, content_text, user_text, message_id)
            messages.append(message)
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
                            self._remove_expired_messages()
                            for message in reversed(messages):
                                if time.time() - message.time < 600:
                                    cache_key = f"{message.sender}_{message.text[:10]}"
                                    if cache_key not in message_cache:
                                        message_cache[cache_key] = message.time
                                        self._run_bound_functions(message)

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
    global user
    
    """ Perform the actual login request """
    logindata = {
        "user": username,
        "pass": password,
        "redirect": ""
    }

    user = username

    response = session.post(actionlogin_url, data=logindata, headers=headers)
    print(f"Response Status Code (ActionLogin): {response.status_code}")

    return response.status_code == 200

def get_key():
    """ Extracts the key needed for Authorization """
    response = session.get(timeline_url, headers=headers)
    match = re.search(r'<input[^>]+name="key"[^>]+value="([^"]+)"', response.text)
    if match:
        return match.group(1)
    return None

# Example Core
get_php_session()
if login(os.environ.get('user'), os.environ.get('pass')):
    # Example client
    binder = FunctionBinder()

    def dolike(message):
        print("Found a message!")
        message.reply(f"||Dit is een automatisch gegenereerd commentaar|| \nOriginele tekst: {message.text}")
    binder.bind(dolike)

    binder.start_checking()
    
    create_post("||This message was automatically generated by a selfbot.||")
