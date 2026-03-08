import asyncio
from curl_cffi.requests import AsyncSession
import json
import logging
import os
from typing import cast
from trader import AvailableTrades, Trader, TraderData, MoxfieldAsset
from config import USERS_FILE

handler = logging.FileHandler(filename='app.log', encoding='utf-8', mode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

class TradeManager:

    traders: dict[str, Trader] = {}

    def __init__(self):

        # Check if users.json exists, create it if not
        if not os.path.exists(f"{USERS_FILE}"):
            with open(f"{USERS_FILE}", "w") as f:
                json.dump({"users": []}, f)

        # Check that it is not empty and has valid format
        try:
            with open(f"{USERS_FILE}", 'r') as f:
                if 'users' not in json.load(f):
                    with open(f"{USERS_FILE}", 'w') as f:
                        json.dump({"users": []}, f)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(f"{USERS_FILE}", "w") as f:
                json.dump({"users": []}, f)

        try:
            with open(f"{USERS_FILE}", 'r+') as f:
                for trader in json.load(f)['users']:
                    trader_data = TraderData({
                        "discord_id": trader["discord_id"],
                        "moxfield_id": trader["moxfield_id"],
                        "moxfield_type": MoxfieldAsset(trader.get("moxfield_type", "collection")),
                    })
                    self.traders[trader_data["discord_id"]] = Trader(**trader_data)
        except (FileNotFoundError, json.JSONDecodeError):
            logging.error("failed to load trader info")

    def get_trader(
        self,
        discord_id: str
    ) -> Trader:
        return self.traders[discord_id]
    
    def add_trader(
        self,
        discord_id: str,
        moxfield_id: str,
        moxfield_type: MoxfieldAsset = MoxfieldAsset.COLLECTION
    ) -> None:

        new_trader = Trader(
            discord_id = discord_id,
            moxfield_id = moxfield_id,
            moxfield_type = moxfield_type
        )
        self.traders[discord_id] = new_trader

    def save_trader_info(self, discord_id: str) -> None:
        current_trader = self.traders[discord_id]
        updated = False
        try:
            with open(f"{USERS_FILE}", 'r') as f:
                all_traders = json.load(f)['users']
                for trader in all_traders:
                    if trader["discord_id"] == discord_id:
                        trader["moxfield_id"] = current_trader.moxfield_id
                        trader["moxfield_type"] = current_trader.moxfield_type.value
                        updated = True

                if updated == False:
                    all_traders.append(
                        {
                            "discord_id": current_trader.discord_id,
                            "moxfield_id": current_trader.moxfield_id,
                            "moxfield_type": current_trader.moxfield_type.value
                        }
                    )
                with open(f"{USERS_FILE}", 'w') as f:
                    json.dump({"users": all_traders}, f, indent=4)
        except (FileNotFoundError, json.JSONDecodeError):
            logging.error("failed to load trader info")

    def remove_trader(self, discord_id: str) -> bool:
        if discord_id not in self.traders:
            return False
        del self.traders[discord_id]
        try:
            with open(f"{USERS_FILE}", 'r') as f:
                all_traders = json.load(f)['users']
            all_traders = [t for t in all_traders if t["discord_id"] != discord_id]
            with open(f"{USERS_FILE}", 'w') as f:
                json.dump({"users": all_traders}, f, indent=4)
        except (FileNotFoundError, json.JSONDecodeError):
            logging.error("failed to save trader info after removal")
        return True

    async def search_for_card(self, card_name: str, active_discord_ids: set[str]) -> AvailableTrades:
        semaphore = asyncio.Semaphore(8)
        available_trades: AvailableTrades = {}

        async def search_trader(session: AsyncSession, trader_id: str):
            async with semaphore:
                trader = self.traders[trader_id]
                found_cards = await trader.search_moxfield(session, card_name)
                if found_cards:
                    available_trades[trader.discord_id] = found_cards

        headers = {"User-Agent": "MtgDiscordTrading"}
        async with AsyncSession(impersonate="chrome", headers=headers) as session, asyncio.TaskGroup() as group:
            for tid in active_discord_ids.intersection(self.traders):
                group.create_task(search_trader(session, tid))

        return available_trades
