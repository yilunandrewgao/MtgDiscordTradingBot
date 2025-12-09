import json
from trader import Trader

class TradeManager:

    traders = {}

    def __init__(self, user_info_file):
        try:
            with open('users.json', 'r') as f:
                data = json.load(f)['users']
                for user_id in data:
                    self.traders[user_id] = Trader(user_id, data[user_id]["echomtg_auth"])

        except (FileNotFoundError, json.JSONDecodeError):
            data = {"users": {}}

    def add_trader(self, discord_id, echomtg_token):

        if discord_id in self.traders:
            print("user already exists")
        
        else:
            new_trader = Trader(discord_id, echomtg_token)
            self.traders[discord_id] = new_trader

    def search_for_card(self, card_name):
        available_trades = {}
        for trader_id in self.traders:
            trader = self.traders[trader_id]
            found_cards = trader.search_collection(card_name)
            if found_cards:
                available_trades[trader.discord_id] = found_cards
        return available_trades