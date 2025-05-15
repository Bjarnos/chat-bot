import dotenv, os
from ChatSelfbot import BotService
bot = BotService.create_bot()

dotenv.load_dotenv()
username = os.environ.get('user')
password = os.environ.get('pass')
if bot.login(username, password):
    messages = bot.MessageService
    messages.create_post("Hello! I am a selfbot :D")
