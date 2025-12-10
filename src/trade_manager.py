import json
import logging
from trader import Trader
from config import USERS_FILE

handler = logging.FileHandler(filename='app.log', encoding='utf-8', mode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

class TradeManager:

    traders = {}

    def __init__(self):
        try:
            with open(USERS_FILE, 'r') as f:
                all_traders = json.load(f)['users']
                for trader in all_traders:
                    self.traders[trader["discord_id"]] = Trader(
                        discord_id = trader["discord_id"],
                        echomtg_token = trader["echomtg_token"],
                        moxfield_id = trader["moxfield_id"]
                    )

        except (FileNotFoundError, json.JSONDecodeError):
            logging.error("failed to load trader info")

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

    def search_for_card(self, card_name):
        available_trades = {}
        for trader_id in self.traders:
            trader = self.traders[trader_id]
            found_cards = trader.search_collection(card_name)
            if found_cards:
                available_trades[trader.discord_id] = found_cards
        return available_trades