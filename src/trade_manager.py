import json
import logging
import os
from trader import Trader
from config import USERS_FILE

handler = logging.FileHandler(filename='app.log', encoding='utf-8', mode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

class TradeManager:

    traders = {}

    def __init__(self):

        # Check if users.json exists, create it if not
        if not os.path.exists(f"src/{USERS_FILE}"):
            with open(f"src/{USERS_FILE}", "w") as f:
                json.dump({"users": []}, f)

        # Check that it is not empty and has valid format
        try:
            with open(f"src/{USERS_FILE}", 'r') as f:
                if 'users' not in json.load(f):
                    with open(f"src/{USERS_FILE}", 'w') as f:
                        json.dump({"users": []}, f)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(f"src/{USERS_FILE}", "w") as f:
                json.dump({"users": []}, f)

        try:
            with open(f"src/{USERS_FILE}", 'r+') as f:
                for trader in json.load(f)['users']:
                    self.traders[trader["discord_id"]] = Trader(
                        discord_id = trader["discord_id"],
                        echomtg_token = trader["echomtg_token"],
                        moxfield_id = trader["moxfield_id"]
                    )
        except (FileNotFoundError, json.JSONDecodeError):
            logging.error("failed to load trader info")

    def get_trader(
        self,
        discord_id
    ): 
        return self.traders[discord_id]
    
    def add_trader(
        self,
        discord_id,
        echomtg_token,
        moxfield_id
    ):

        new_trader = Trader(
            discord_id = discord_id,
            echomtg_token = echomtg_token,
            moxfield_id = moxfield_id
        )
        self.traders[discord_id] = new_trader

    def save_trader_info(self, discord_id):
        current_trader = self.traders[discord_id]
        updated = False
        try:
            with open(f"src/{USERS_FILE}", 'r') as f:
                all_traders = json.load(f)['users']
                for trader in all_traders:
                    if trader["discord_id"] == discord_id:
                        trader["echomtg_token"] = current_trader.echomtg_token
                        trader["moxfield_id"] = current_trader.moxfield_id
                        updated = True
                
                if updated == False:
                    all_traders.append(
                        {
                            "discord_id": current_trader.discord_id,
                            "echomtg_token": current_trader.echomtg_token,
                            "moxfield_id": current_trader.moxfield_id
                        }
                    )
                with open(f"src/{USERS_FILE}", 'w') as f:
                    json.dump({"users": all_traders}, f, indent=4)
        except (FileNotFoundError, json.JSONDecodeError):
            logging.error("failed to load trader info")

    def search_for_card(self, card_name, active_discord_ids):
        available_trades = {}
        for trader_id in self.traders:
            if trader_id in active_discord_ids:
                trader = self.traders[trader_id]
                found_cards = trader.search_moxfield(card_name)
                if found_cards:
                    available_trades[trader.discord_id] = found_cards
        return available_trades