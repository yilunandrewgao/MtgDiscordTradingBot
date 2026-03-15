import asyncio
from collections.abc import Sequence
from curl_cffi.requests import AsyncSession
import json
import logging
import os
from trader import AvailableTrades, CardEntry, Trader, TraderData, MoxfieldAsset
from decklist_parser import CardQuery, Printing
from config import USERS_FILE

_BATCH_SIZE = 50

_FINISH = {
    Printing.Normal: 'nonFoil',
    Printing.Foil: 'foil',
    Printing.EtchedFoil: 'etched',
}

handler = logging.FileHandler(filename='app.log', encoding='utf-8', mode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


class TraderNotFound(Exception):
    ...


class TradeManager:

    _traders: dict[str, Trader]

    def __init__(self):
        self._traders = {}

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
                        "wishlist_id": trader.get("wishlist_id"),
                    })
                    self._traders[trader_data["discord_id"]] = Trader(**trader_data)
        except (FileNotFoundError, json.JSONDecodeError):
            logging.error("failed to load trader info")

    def get_trader(self, discord_id: str) -> Trader | None:
        return self._traders.get(discord_id)

    def upsert_trader(
        self,
        discord_id: str,
        moxfield_id: str,
        moxfield_type: MoxfieldAsset = MoxfieldAsset.COLLECTION
    ) -> None:
        if discord_id in self._traders:
            trader = self._traders[discord_id]
            trader.moxfield_id = moxfield_id
            trader.moxfield_type = moxfield_type
        else:
            self._traders[discord_id] = Trader(
                discord_id=discord_id,
                moxfield_id=moxfield_id,
                moxfield_type=moxfield_type,
            )
        self.save_trader_info(discord_id)

    def save_trader_info(self, discord_id: str) -> None:
        current_trader = self._traders[discord_id]
        updated = False
        try:
            with open(f"{USERS_FILE}", 'r') as f:
                all_traders = json.load(f)['users']
                for trader in all_traders:
                    if trader["discord_id"] == discord_id:
                        trader["moxfield_id"] = current_trader.moxfield_id
                        trader["moxfield_type"] = current_trader.moxfield_type.value
                        trader.pop("wishlist_id", None)
                        if current_trader.wishlist_id is not None:
                            trader["wishlist_id"] = current_trader.wishlist_id
                        updated = True

                if updated == False:
                    entry: dict = {
                        "discord_id": current_trader.discord_id,
                        "moxfield_id": current_trader.moxfield_id,
                        "moxfield_type": current_trader.moxfield_type.value,
                    }
                    if current_trader.wishlist_id is not None:
                        entry["wishlist_id"] = current_trader.wishlist_id
                    all_traders.append(entry)
                with open(f"{USERS_FILE}", 'w') as f:
                    json.dump({"users": all_traders}, f, indent=4)
        except (FileNotFoundError, json.JSONDecodeError):
            logging.error("failed to load trader info")

    def set_wishlist(self, discord_id: str, wishlist_id: str | None) -> Trader:
        if discord_id not in self._traders:
            raise TraderNotFound(discord_id)
        self._traders[discord_id].wishlist_id = wishlist_id
        self.save_trader_info(discord_id)
        return self._traders[discord_id]

    def remove_wishlist(self, discord_id: str) -> bool:
        if discord_id not in self._traders:
            raise TraderNotFound(discord_id)
        if self._traders[discord_id].wishlist_id is None:
            return False
        self._traders[discord_id].wishlist_id = None
        self.save_trader_info(discord_id)
        return True

    def remove_trader(self, discord_id: str) -> bool:
        if discord_id not in self._traders:
            return False
        del self._traders[discord_id]
        try:
            with open(f"{USERS_FILE}", 'r') as f:
                all_traders = json.load(f)['users']
            all_traders = [t for t in all_traders if t["discord_id"] != discord_id]
            with open(f"{USERS_FILE}", 'w') as f:
                json.dump({"users": all_traders}, f, indent=4)
        except (FileNotFoundError, json.JSONDecodeError):
            logging.error("failed to save trader info after removal")
        return True

    async def search_for_card(self, card_name: str, active_discord_ids: set[str], finish: str | None = None) -> AvailableTrades:
        semaphore = asyncio.Semaphore(8)
        available_trades: AvailableTrades = {}

        async def search_trader(session: AsyncSession, trader_id: str):
            async with semaphore:
                trader = self._traders[trader_id]
                found_cards = await trader.search_moxfield(session, card_name, finish)
                if found_cards:
                    available_trades[trader.discord_id] = found_cards

        headers = {"User-Agent": "MtgDiscordTrading"}
        async with AsyncSession(impersonate="chrome", headers=headers) as session, asyncio.TaskGroup() as group:
            for tid in active_discord_ids.intersection(self._traders):
                group.create_task(search_trader(session, tid))

        return available_trades

    async def batched_search(self, queries: Sequence[tuple[str, str | None]], discord_ids: set[str]) -> AvailableTrades:
        tasks: list[asyncio.Task[AvailableTrades]] = []
        async with asyncio.TaskGroup() as group:
            for query, finish in queries:
                tasks.append(group.create_task(
                    self.search_for_card(query, discord_ids, finish=finish)
                ))
        merged: dict[str, dict[str, CardEntry]] = {}
        for task in tasks:
            for discord_id, found in task.result().items():
                merged.setdefault(discord_id, {}).update(found)
        return merged

    async def fuzzy_search(self, cards: list[CardQuery], discord_ids: set[str]) -> AvailableTrades:
        queries = [
            (' or '.join(f'"{card.name}"' for card in cards[i:i + _BATCH_SIZE]), None)
            for i in range(0, len(cards), _BATCH_SIZE)
        ]
        return await self.batched_search(queries, discord_ids)

    async def exact_search(self, cards: list[CardQuery], discord_ids: set[str]) -> AvailableTrades:
        partitions: dict[Printing, list[CardQuery]] = {}
        for card in cards:
            partitions.setdefault(card.printing, []).append(card)

        queries = [
            (' or '.join(card.to_moxfield_query() for card in partition[i:i + _BATCH_SIZE]), _FINISH[printing])
            for printing, partition in partitions.items()
            for i in range(0, len(partition), _BATCH_SIZE)
        ]
        return await self.batched_search(queries, discord_ids)
