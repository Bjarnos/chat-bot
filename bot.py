# This script was written with a Docs AI, coming soon!
import dotenv
import os
import random
from ChatSelfbot import BotService, Classes

dotenv.load_dotenv()

bot = BotService.create_bot()
username = os.environ.get('user')
password = os.environ.get('pass')

if bot.login(username, password):
    connections = bot.ConnectionService
    messages = bot.MessageService

    # Local variables for storing player data
    player_data = {}

    def start_game(message: Classes.DMMessage):
        player_id = message.sender_id
        if player_id not in player_data:
            player_data[player_id] = {'cash': 0, 'sword_damage': 1}
            messages.reply(message.id, "Welcome to the RPG! You can battle monsters to earn cash.")
        else:
            messages.reply(message.id, "You are already in the game! Type 'battle' to fight a monster.")

    def battle(message: Classes.DMMessage):
        player_id = message.sender_id
        if player_id not in player_data:
            messages.reply(message.id, "You need to start the game first! Type 'start' to begin.")
            return
        
        monster_health = random.randint(5, 15)
        player_damage = player_data[player_id]['sword_damage']
        
        while monster_health > 0:
            monster_health -= player_damage
            if monster_health <= 0:
                player_data[player_id]['cash'] += 10  # Reward for defeating the monster
                messages.reply(message.id, f"You defeated the monster! You earned 10 cash. Total cash: {player_data[player_id]['cash']}")
                return
            # Simulate monster attack (optional)
            messages.reply(message.id, f"The monster has {monster_health} health left. You deal {player_damage} damage!")

    def buy_sword(message: Classes.DMMessage):
        player_id = message.sender_id
        if player_id not in player_data:
            messages.reply(message.id, "You need to start the game first! Type 'start' to begin.")
            return
        
        if player_data[player_id]['cash'] >= 50:  # Cost of the sword
            player_data[player_id]['sword_damage'] += 1
            player_data[player_id]['cash'] -= 50
            messages.reply(message.id, f"You bought a sword! Your damage is now {player_data[player_id]['sword_damage']}.")
        else:
            messages.reply(message.id, "You don't have enough cash to buy a sword.")

    def handle_message(message: Classes.DMMessage):
        if message.content.lower() == 'start':
            start_game(message)
        elif message.content.lower() == 'battle':
            battle(message)
        elif message.content.lower() == 'buy sword':
            buy_sword(message)
        else:
            messages.reply(message.id, "Type 'start' to begin the game, 'battle' to fight, or 'buy sword' to purchase a sword.")

    connections.bind_to_any_dm(handle_message)
    connections.start_checking_dms()  # Required to check for new DMs
