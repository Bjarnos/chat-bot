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
saved_key = None

# Public API
user = None

def create_post(message=False):
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
    if not message_id or not message:
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

# Core modules
class Message:
    def __init__(self, time, text, sender, id, reactions):
        self.time = format_time(time)
        self.text = text
        self.sender = sender
        self.id = str(id)
        self.reactions = reactions

    def like(self, value=True):
        like(self.id, value)

    def reply(self, message=False):
        reply(self.id, message)

    def bind_to_reply(self, func=False):
        binder.bind_to_message_reply(self.id, func)
    
    def get_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.time))

class BinderService:
    def __init__(self):
        self.functions = []
        self.reply_functions = {}
        self.is_checking = False

    def bind_to_message_post(self, func):
        self.functions.append(func)

    def bind_to_message_reply(self, message_id, func):
        if message_id not in self.reply_functions:
            self.reply_functions[message_id] = []
        self.reply_functions[message_id].append(func)

    def _run_bound_functions(self, message):
        for func in self.functions:
            func(message)

    def _run_bound_functions_to_reply(self, message):
        if message.id in self.reply_functions:
            for func in self.reply_functions[message.id]:
                func(message)

    def start_checking(self):
        if not self.is_checking:
            self.is_checking = True
            threading.Thread(target=self._check_periodically).start()

    def _check_periodically(self):
        while self.is_checking:
            try:
                response = requests.get(timeline_url, headers=headers)
                if response.status_code == 200:
                    messages = extract_messages(response.text)
                    def handle_message_list(messages, first):
                        for message in messages:
                            if time.time() - message.time < 600 and message.id not in message_cache:
                                print(time.time() - message.time)
                                message_cache[message.id] = message.time
                                if first:
                                    self._run_bound_functions(message)
                                else:
                                    self._run_bound_functions_to_reply(message)
                                handle_message_list(message.reactions, False)
                    
                    handle_message_list(messages, True)
            except Exception as e:
                print(f"Error checking for new posts: {e}")
            time.sleep(10)

    def stop_checking(self):
        self.is_checking = False

def format_time(timestr):
    match = re.match(r"(\d+)\s*(second|minute)s?", timestr.strip().lower())
    
    if not match:
        return "Invalid time format"
    
    number = int(match.group(1))
    unit = match.group(2)
    
    if unit == "second":
        return time.time() - number
    elif unit == "minute":
        return time.time() - number * 60
    else:
        return 0

def extract_messages(html):
    def parse_message(message_container):
        message_div = message_container.find('div', class_='message')
        time_element = message_div.find('p', class_='time')
        content_element = message_div.find('div', class_='content')
        user_element = message_div.find('a', class_='username')
        message_id_element = message_div.find('button', class_='submit inverted message-menu-share-button')
        message_id = message_id_element['data-id'] if message_id_element else None
    
        reactions = [parse_message(reaction_div) for reaction_div in message_container.find('div', class_='reactions').find_all('div', class_='reaction')]

        return Message(time_element.text.strip() if content_element else "", content_element.text.strip() if content_element else "", user_element.text.strip() if user_element else "Unknown", message_id if message_id else "0", reactions if reactions else [])
        
    soup = BeautifulSoup(html, 'html.parser')
    return [parse_message(message_div) for message_container in soup.find_all('div', class_='message-container')]

# Core API
def get_php_session():
    session.get(login_url, headers=headers)

def login(username, password):
    global user
    user = username
    logindata = {"user": username, "pass": password, "redirect": ""}
    response = session.post(actionlogin_url, data=logindata, headers=headers)
    return response.status_code == 200

def get_key():
    global saved_key
    if saved_key:
        return saved_key
    
    response = session.get(timeline_url, headers=headers)
    match = re.search(r'<input[^>]+name="key"[^>]+value="([^\"]+)"', response.text)
    saved_key = match.group(1) if match else None
    return saved_key

# Example code
get_php_session()
if login(os.environ.get('user'), os.environ.get('pass')):
    binder = BinderService()
    def replyhello(message):
        message.reply("Hello! #2")
    def dolike(message):
        message.like()
        message.bind_to_reply(replyhello)
    binder.bind_to_message_post(dolike)
    binder.start_checking()
    #create_post("||This message was generated with SelfbotV1||")
