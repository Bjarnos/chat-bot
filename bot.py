# Imports
import requests
import re
import time
import threading
from bs4 import BeautifulSoup
from datetime import datetime

# Preloads
session = requests.Session()

# Constants
base = "chat.jonazwetsloot.nl"
url = f"https://{base}"
api_url = f"{url}/api/v1"
login_url = f"{url}/login"
actionlogin_url = f"{url}/actionlogin"
timeline_url = f"{url}/timeline"
inbox_url = f"{url}/inbox"
list_dms_url = f"{url}/messages"
send_message_url = f"{api_url}/message"
dm_url = f"{api_url}/direct-message"
group_url = f"{api_url}/group-message"
like_url = f"{api_url}/like"

version = "Selfbot V1.0.0"

headers = { 
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8,application/json,text/plain,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Host": base,
    "Origin": url,
    "Referer": login_url,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Content-Type": "application/x-www-form-urlencoded",
}

# Variables
message_cache = {}
dm_cache = {}
dm_cache_user = {}
saved_key = None
first_run = True
show_http = True

# Functions
user = None

def show_message(message=None, mtype="Standard"):
    if not message:
        return
    
    if mtype == "Standard":
        print(f"[{version}] {message}")
    elif mtype == "Error":
        print(f"[{version}] Error: {message}")
    elif mtype == "Http" and show_http:
        print(f"[{version}] Http: {message}")

def reply(message_id=None, message=None):
    if not message_id or not message:
        return
    
    key = get_key()
    if not key:
        return

    data = {
        "message": message,
        "id": message_id,
        "name": user,
        "key": key
    }
    response = session.post(send_message_url, data=data, headers=headers)
    show_message(f"Response Status Code (Send Reply): {response.status_code}", "Http")

def like(message_id=None, value=True):
    if not message_id:
        return
    
    key = get_key()
    if not key:
        return
    
    data = {
        "id": message_id,
        "like": str(value).lower(),
        "name": user,
        "key": key
    }
    response = session.post(like_url, data=data, headers=headers)
    show_message(f"Response Status Code (Like Message): {response.status_code}", "Http")

def direct_message(username=None, message=None):
    if not username or not message:
        return
    
    key = get_key()
    if not key:
        return
    
    data = {
        "attachments": "",
        "name": user,
        "key": key,
        "user": username,
        "message": message
    }
    response = session.post(dm_url, data=data, headers=headers)
    show_message(f"Response Status Code (Direct Message): {response.status_code}", "Http")

    
def group_message(groupid=None, message=None):
    if not groupid or not message:
        return
    
    key = get_key()
    if not key:
        return
    
    data = {
        "attachments": "",
        "name": user,
        "key": key,
        "id": groupid,
        "message": message
    }
    response = session.post(group_url, data=data, headers=headers)
    show_message(f"Response Status Code (Group Message): {response.status_code}", "Http")

def get_text_from_message(message_div=None):
    if not message_div:
        return ""
    
    result_text = ""
    
    for child in message_div.descendants:
        if child.name is None:
            result_text += child
        elif child.name == "span":
            result_text += child.get_text(strip=True)
        elif child.name == "img":
            result_text += child.get("alt", "")
    
    return result_text

def format_time(timestr):
    match = re.match(r"(\d+)\s*(second|minute)s?", timestr.strip().lower())
    
    if not match:
        return 0
    
    number = int(match.group(1))
    unit = match.group(2)
    
    if unit == "second":
        return time.time() - number
    elif unit == "minute":
        return time.time() - number * 60
    else:
        return 0
    
from datetime import datetime, timedelta

def format_real_time(timestr):
    if timestr:
        try:
            time_obj = datetime.strptime(timestr, "%H:%M")
            now = datetime.now()
            
            target_time = now.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
            
            if target_time < now:
                target_time = target_time + timedelta(days=1)

            time_diff = target_time - now
            return int(time_diff.total_seconds())
        except ValueError:
            show_message(f"Invalid DM time format: {timestr}", "Error")
            return 0
    else:
        return 0

    
def format_date(datestr):
    if datestr == "Today":
        return datetime.today().strftime("%d/%m/%y")
    elif datestr == "Yesterday":
        return (datetime.today() - timedelta(days=1)).strftime("%d/%m/%y")
    else:
        return datestr

def extract_messages(html):
    def parse_message(message_container, parent_id=None):
        message_div = None
        if parent_id:
            message_div = message_container
        else:
            message_div = message_container.find('div', class_='message')
        
        if not message_div:
            show_message("Message div doesn't exist!", "Error")
            return None

        bar_div = message_div.find('div', class_='bar')
        if not bar_div:
            show_message("Bar div doesn't exist!", "Error")
            return None

        time_element = bar_div.find('p', class_='time')
        content_element = message_div.find('div', class_='content')
        user_element = bar_div.find('a', class_='username')
        message_id_element = bar_div.find('button', class_='submit inverted message-menu-share-button')

        message_id = message_id_element['data-id'] if message_id_element else "0"
        time_text = time_element.text.strip() if time_element else ""
        content_text = " ".join([p.text.strip() for p in content_element.find_all('p')]) if content_element else ""
        user_text = user_element.text.strip() if user_element else "Unknown"

        reactions_container = message_container.find('div', class_='reactions')
        reactions = []
        if reactions_container:
            reactions = [parse_message(reaction_div, message_id) for reaction_div in reactions_container.find_all('div', class_='reaction') if reaction_div]

        return PublicMessage(format_time(time_text), content_text, user_text, message_id, reactions, parent_id)

    soup = BeautifulSoup(html, 'html.parser')
    messages = [parse_message(message_container) for message_container in soup.find_all('div', class_='message-container')]

    return [msg for msg in messages if msg is not None]

# Core objects
class PublicMessage:
    def __init__(self, time, text, sender, id, reactions, parent_id):
        self.time = float(time)     # 0 in old public messages
        self.text = text
        self.sender = sender
        self.id = str(id)

        self.reactions = reactions
        self.parent_id = parent_id

    def like(self, value=True):
        like(self.id, value)

    def reply(self, message=None):
        reply(self.id, message)

    def bind_to_reply(self, func=None):
        print("binding")
        Core_BotService.ConnectionService.bind_to_message_reply(self.id, func)
        print(Core_BotService.ConnectionService.reply_functions)

class DMMessage:
    def __init__(self, time, text, sender, id, groupname, groupid):
        self.time = float(time)     # 0 in any-user dms
        self.text = text
        self.sender = sender
        self.id = str(id)           # "0" in any-user dms
        self.groupname = groupname  # None in normal dms
        self.groupid = groupid      # None in normal dms

    def reply(self, message=None):
        if self.groupid:
            group_message(self.groupid, message)
        else:
            direct_message(self.sender, message)

# Core services
class ConnectionService:
    # Core:
    def __init__(self):
        self.public_functions = []
        self.reply_functions = {}
        self.is_checking_public = False

        self.anydm_functions = []
        self.userdm_functions = {}
        self.is_checking_dms = False

    # Core public:
    def _run_bound_functions(self, message):
        if message is not None:
            if first_run and message.sender == user:
                return
            
            for func in self.public_functions:
                func(message)

    def _run_bound_functions_to_reply(self, message, parent_id):
        if message is not None and parent_id is not None:
            print("??")
            if first_run and message.sender == user:
                print("returning!")
                return

            print(self.reply_functions)
            if self.reply_functions.get(parent_id):
                print("yes")
                for func in self.reply_functions[parent_id]:
                    func(message)

    def start_checking_public(self):
        if not self.is_checking_public:
            self.is_checking_public = True
            threading.Thread(target=self._check_periodically_public).start()

    def _check_periodically_public(self):
        global first_run
        while self.is_checking_public:
            try:
                show_message("Checking public...")
                response = requests.get(timeline_url, headers=headers)
                if response.status_code == 200:
                    messages = extract_messages(response.text)
                    def handle_message_list(messages, first):
                        for message in messages:
                            if message != None:
                                if time.time() - message.time < 600 and message.id not in message_cache:
                                    message_cache[message.id] = message.time
                                    if first:
                                        self._run_bound_functions(message)
                                    else:
                                        print("any reply found")
                                        print(message.id)
                                        print(message.parent_id)
                                        self._run_bound_functions_to_reply(message, message.parent_id)
                                handle_message_list(message.reactions, False)
                            else:
                                show_message("Message is None", "Error")
                    
                    handle_message_list(messages, True)

                self.check_public_cache()
                first_run = False
            except Exception as e:
                show_message(f"Error checking for new public posts: {e}", "Error")
            time.sleep(10)

    def stop_checking_public(self):
        self.is_checking_public = False

    def check_public_cache(self):
        to_delete = [id for id, unix in message_cache.items() if time.time() - unix > 600]
        for id in to_delete:
            del message_cache[id]

    # Core DM:
    def _run_dm_functions(self, message):
        if message is not None:
            for func in self.anydm_functions:
                func(message)

    def _run_dm_functions_from_user(self, message):
        if message is not None and self.userdm_functions[message.sender]:
            for func in self.userdm_functions[message.sender]:
                func(message)

    def start_checking_dms(self):
        if not self.is_checking_dms:
            self.is_checking_dms = True
            threading.Thread(target=self._check_periodically_dms).start()

    def _check_periodically_dms(self):
        while self.is_checking_dms:
            try:
                show_message("Checking DMs...")
                response = session.post(inbox_url, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    for user_contact in soup.find_all('a', class_='user-contact'):
                        name = user_contact.find('h3').text.strip()
                        groupname = None
                        newestmessage_element = user_contact.find('p')
                        b = newestmessage_element.find('b')
                        if b:
                            if name != b.text.strip():
                                groupname = name
                            name = b.text.strip()
                            b.decompose()
                        newestmessage = newestmessage_element.text.strip()
                        if newestmessage == "You have not yet sent any messages to this person.":
                            continue

                        if user_contact.find('img', class_='info'):
                            if not dm_cache.get(name):
                                dm_cache[name] = "[empty]"
                            continue

                        if not dm_cache.get(name):
                            dm_cache[name] = newestmessage
                        elif dm_cache[name] != newestmessage:
                            dm_cache[name] = newestmessage
                            self._run_dm_functions(DMMessage("0", newestmessage, name, "0", groupname))

                for username, functions in self.userdm_functions.items():
                    response = session.get(f'{list_dms_url}/{username}', headers=headers)
                    soup = BeautifulSoup(response.text, "html.parser")
                    offset = 0
                    for message_box in soup.find_all('div', class_='receiver'):
                        offset += 1
                        message_box = message_box.find('div', class_='dm')
                        id = message_box['data-id']
                        if dm_cache_user.get(id):
                            continue

                        time_literal = message_box.find('p', class_='time').text.strip()

                        time_day = ""
                        date_span = message_box.find_previous('span', class_='date')
                        if date_span:
                            time_day = date_span.text.strip()
                        else:
                            time_day = "Today"

                        datestr = f"{format_date(time_day)} {time_literal}"
                        unix = int(datetime.strptime(datestr, "%d/%m/%y %H:%M").timestamp()) + offset

                        if time.time() - unix < 600:
                            dm_cache_user[id] = unix

                            name = message_box.find('a', class_='username').text.strip()
                            text = get_text_from_message(message_box.find('div', class_='content'))

                            message = DMMessage(unix, text, name, id, None)
                            for func in functions:
                                func(message)

                    self.check_dm_cache()
            except Exception as e:
                show_message(f"Error checking for new dm posts: {e}", "Error")
            time.sleep(10)

    def stop_checking_dms(self):
        self.is_checking_dms = False

    def check_dm_cache(self):
        to_delete = [id for id, unix in dm_cache_user.items() if time.time() - unix > 600]
        for id in to_delete:
            del dm_cache_user[id]

    # Public service:
    def bind_to_public_post(self, func):
        self.public_functions.append(func)

    def bind_to_message_reply(self, message_id, func):
        print("abc")
        if message_id not in self.reply_functions:
            self.reply_functions[message_id] = []
        self.reply_functions[message_id].append(func)
        print(self.reply_functions)

    # DM Service:
    def bind_to_any_dm(self, func):
        self.anydm_functions.append(func)

    def bind_to_user_dm(self, username, func):
        username = username.replace(' ', '-')
        if username not in self.userdm_functions:
            self.userdm_functions[username] = []
        self.userdm_functions[username].append(func)

class MessageService:
    def create_post(self, message=None):
        if not message:
            return
    
        key = get_key()
        if not key:
            return

        data = {
            "message": message,
            "attachments": "",
            "name": user,
            "key": key
        }
        response = session.post(send_message_url, data=data, headers=headers)
        show_message(f"Response Status Code (Send Message): {response.status_code}", "Http")

    def reply(self, message_id=None, message=None):
        reply(message_id, message)

    def like(self, message_id=None, value=True):
        like(message_id, value)

    def direct_message(self, username=None, message=None):
        direct_message(username, message)

    def get_group_id_by_name(self, groupname=None):
        if not groupname:
            return
        
        response = session.post(inbox_url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            for user_contact in soup.find_all('a', class_='user-contact'):
                name = user_contact.find('h3').text.strip()
                if name == groupname:
                    href = user_contact.get('href')
                    if href:
                        id = href.split("/")[-1]
                        return id

    def group_message_by_name(self, groupname=None, message=None):
        groupid = self.get_group_id_by_name(groupname)
        if groupid:
            group_message(groupid, message)

    def group_message_by_id(self, groupid=None, message=None):
        group_message(groupid, message)

class BotService:
    def __init__(self):
        self.ConnectionService = ConnectionService()
        self.MessageService = MessageService()

    def start_session(self):
        session.get(login_url, headers=headers)

    def login(self, username, password):
        global user
        self.start_session()

        user = username
        logindata = {"user": username, "pass": password, "redirect": ""}
        response = session.post(actionlogin_url, data=logindata, headers=headers)
        return response.status_code == 200

# Core API
def get_key():
    global saved_key
    if saved_key:
        return saved_key
    
    response = session.get(timeline_url, headers=headers)
    match = re.search(r'<input[^>]+name="key"[^>]+value="([^\"]+)"', response.text)
    saved_key = match.group(1) if match else None
    if saved_key == None:
        show_message("Failed to retrieve key.", "Error")
    return saved_key

show_message("Library succesfully loaded.")

Core_BotService = BotService()
# Normally, Core_BotService would be exported!

# Example code
bot = Core_BotService
if bot.login("Bjarnos", "RobloxUserBjarnos24"):
    connections = Core_BotService.ConnectionService
    messages = Core_BotService.MessageService
    def f2(message):
        message.like()
        message.reply("Hier heb je een like!")
        messages.direct_message(message.sender, "Hallo! Leuk dat je op het bericht hebt gereageerd. Laat hier commentaar op de bot achter zodat ik hem kan verbeteren :).")
    def f1(message):
        if message.text == "Hallo! Ik ben een selfbot. Reageer op dit bericht voor een gratis like :D\n||This message was generated with SelfbotV1||":
            message.bind_to_reply(f2)
    connections.bind_to_public_post(f1)
    connections.start_checking_public()
    messages.create_post("Hallo! Ik ben een selfbot. Reageer op dit bericht voor een gratis like :D\n||This message was generated with SelfbotV1||")
