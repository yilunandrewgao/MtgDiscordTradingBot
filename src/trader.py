from curl_cffi.requests import AsyncSession
import logging
from typing import Mapping, NotRequired, TypedDict
from models.moxfield_types import MoxfieldAsset
from moxfield_api import call_moxfield_api


handler = logging.FileHandler(filename='app.log', encoding='utf-8', mode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

class TraderData(TypedDict):
    discord_id: str
    moxfield_id: str
    moxfield_type: NotRequired[MoxfieldAsset]

class CardEntry(TypedDict):
    count: int
    name: str | None
    expansion: str | None
    scryfall_id: str | None
    cn: str | None

AvailableTrades = Mapping[str, Mapping[str, CardEntry]]

class Trader:
    
    def __init__(
        self,
        discord_id: str,
        moxfield_id: str,
        moxfield_type: MoxfieldAsset = MoxfieldAsset.COLLECTION
    ):
        self.discord_id: str = discord_id
        self.moxfield_id: str = moxfield_id
        self.moxfield_type: MoxfieldAsset = moxfield_type

    
    async def get_moxfield_session_id(self, session: AsyncSession, card_name: str) -> str:

        params: dict[str, str | int] = {
            "pageSize": 1,
            "q": card_name
        }

        response = await call_moxfield_api(session=session, moxfield_id=self.moxfield_id, moxfield_type=self.moxfield_type, params=params)

        session_id = response.get("searchSessionId", None)

        if not session_id:
            raise Exception(f"Failed to get search session ID for {self.moxfield_id} and card {card_name}")

        return session_id

    async def search_moxfield(self, session: AsyncSession, card_name: str, finish: str | None = None) -> dict[str, CardEntry]:

        session_id = await self.get_moxfield_session_id(session, card_name)

        params: dict[str, str | int] = {
            "pageSize": 1000,
            "q": card_name,
            "searchSessionId": session_id
        }
        if finish is not None:
            params["finish"] = finish

        response = await call_moxfield_api(session=session, moxfield_id=self.moxfield_id, moxfield_type=self.moxfield_type, params=params)

        return self.group_cards_by_id(response)
    
    def group_cards_by_id(self, moxfield_response) -> dict[str, CardEntry]:

        grouped_items: dict[str, CardEntry] = {}

        for entry in moxfield_response['data']:
            card = entry.get("card", {})
            id = entry.get("id")
            quantity = entry.get("quantity", 1)

            if id not in grouped_items:
                grouped_items[id] = {
                    "count": quantity,
                    "name": card.get("name"),
                    "expansion": card.get("set_name"),
                    "scryfall_id": card.get("scryfall_id"),
                    "cn": card.get("cn")
                }
            else:
                grouped_items[id]["count"] += quantity

        return grouped_items
