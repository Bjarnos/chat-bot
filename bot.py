import dotenv, os
from ChatSelfbot import BotService
DMMessage = Classes.DMMessage
bot = BotService.create_bot()

dotenv.load_dotenv()
username = os.environ.get('user')
password = os.environ.get('pass')
if bot.login(username, password):
    connections = bot.ConnectionService
    messages = bot.MessageService

    players = {}

    def start_game(username):
        players[username] = {
            'health': 100,
            'cash': 0,
            'weapon': 'Wooden Sword',
            'damage': 10
        }
        return f"Welcome to the RPG, {username}! You have started with a {players[username]['weapon']}."

    def battle(username):
        if username not in players:
            return "You need to start the game first! Type 'start' to begin."
        
        monster_health = 50
        player_damage = players[username]['damage']
        
        while monster_health > 0 and players[username]['health'] > 0:
            attack = random.randint(5, player_damage)
            monster_health -= attack
            response = f"You dealt {attack} damage to the monster! Monster health: {monster_health}"
            
            if monster_health <= 0:
                players[username]['cash'] += 20
                return response + f"\nYou defeated the monster! You earned 20 cash. Total cash: {players[username]['cash']}"
            
            monster_attack = random.randint(5, 15)
            players[username]['health'] -= monster_attack
            response += f"\nThe monster attacked you for {monster_attack} damage! Your health: {players[username]['health']}"
            
            if players[username]['health'] <= 0:
                return response + "\nYou have been defeated! Game over."
        
        return response

    def f1(message: DMMessage):
        username = message.sender.username
        content = message.content.lower()

        if content == 'start':
            response = start_game(username)
        elif content == 'battle':
            response = battle(username)
        else:
            response = "Type 'start' to begin your adventure or 'battle' to fight a monster."

        message.reply(response)

    connections.bind_to_any_dm(f1)
    connections.start_checking_dms()  # required!
