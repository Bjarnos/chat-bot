import dotenv, os
from ChatSelfbot import BotService
bot = BotService.create_bot()

dotenv.load_dotenv()
username = os.environ.get('user')
password = os.environ.get('pass')
if bot.login(username, password):
    connections = bot.ConnectionService
    def f1(message):
        print("message?")
        print(message.sender)
        if message.sender == "Bjarnos":
            message.reply("Hi Bjarnos!\n-# This message was created with a selfbot.")
    connections.bind_to_public_post(f1)
