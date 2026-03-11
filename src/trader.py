from curl_cffi.requests import AsyncSession, RequestsError
from curl_cffi import requests as curl_requests
import logging
import json
from typing import Any, Mapping, NotRequired, TypedDict
from models.moxfield_types import MoxfieldAsset


handler = logging.FileHandler(filename='app.log', encoding='utf-8', mode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

class TraderData(TypedDict):
    discord_id: str
    moxfield_id: str
    moxfield_type: NotRequired[MoxfieldAsset]
    wishlist_id: NotRequired[str | None]

class CardEntry(TypedDict):
    count: int
    name: str | None
    expansion: str | None
    scryfall_id: str | None
    cn: str | None

AvailableTrades = Mapping[str, Mapping[str, CardEntry]]

def call_moxfield_api_sync(
    moxfield_id: str,
    moxfield_type: MoxfieldAsset = MoxfieldAsset.COLLECTION,
    params: dict[str, str | int] | None = None
) -> dict[str, Any]:

    if moxfield_type == MoxfieldAsset.BINDER:
        url = f"https://api2.moxfield.com/v1/trade-binders/{moxfield_id}/search"
    else:
        url = f"https://api2.moxfield.com/v1/collections/search/{moxfield_id}"

    try:
        response = curl_requests.get(
            url,
            headers={
                "User-Agent": "MtgDiscordTrading",
                "Host": "api2.moxfield.com",
            },
            params=params,
            impersonate="chrome"
        )
        response.raise_for_status()
        if not response.text:
            logging.debug(f"Failed to call moxfield using collection id: {moxfield_id}")
            return {}
        return response.json()

    except RequestsError as e:
        raise Exception(f"Failed to fetch collection {moxfield_id}: {e}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON response for {moxfield_id}: {e}")

async def call_moxfield_api(
    session: AsyncSession,
    moxfield_id: str,
    moxfield_type: MoxfieldAsset = MoxfieldAsset.COLLECTION,
    params: dict[str, str | int] | None = None
) -> dict[str, Any]:

    if moxfield_type == MoxfieldAsset.BINDER:
        url = f"https://api2.moxfield.com/v1/trade-binders/{moxfield_id}/search"
    else:
        url = f"https://api2.moxfield.com/v1/collections/search/{moxfield_id}"

    try:
        response = await session.get(url, params=params)
        response.raise_for_status()
        if not response.text:
            logging.debug(f"Failed to call moxfield using collection id: {moxfield_id}")
            return {}
        return response.json()

    except RequestsError as e:
        raise Exception(f"Failed to fetch collection {moxfield_id}: {e}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON response for {moxfield_id}: {e}")

class Trader:
    
    def __init__(
        self,
        discord_id: str,
        moxfield_id: str,
        moxfield_type: MoxfieldAsset = MoxfieldAsset.COLLECTION,
        wishlist_id: str | None = None
    ):
        self.discord_id: str = discord_id
        self.moxfield_id: str = moxfield_id
        self.moxfield_type: MoxfieldAsset = moxfield_type
        self.wishlist_id: str | None = wishlist_id

    @property
    def wishlist_url(self) -> str | None:
        if self.wishlist_id:
            return f"https://moxfield.com/decks/{self.wishlist_id}"
        return None

    
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

