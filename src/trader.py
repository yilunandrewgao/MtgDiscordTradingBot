from curl_cffi.requests import AsyncSession, RequestsError
import logging
import json
from typing import Any, Literal, Mapping, NotRequired, TypedDict


handler = logging.FileHandler(filename='app.log', encoding='utf-8', mode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

MoxfieldType = Literal["collection", "binder"]

class TraderData(TypedDict):
    discord_id: str
    moxfield_id: str
    moxfield_type: NotRequired[MoxfieldType]

class CardEntry(TypedDict):
    count: int
    name: str | None
    expansion: str | None
    scryfall_id: str | None
    cn: str | None

AvailableTrades = Mapping[str, Mapping[str, CardEntry]]

async def call_moxfield_api(session: AsyncSession, moxfield_id: str, moxfield_type: MoxfieldType = "collection", params: dict[str, str | int] | None = None) -> dict[str, Any]:

    if moxfield_type == "binder":
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
        moxfield_type: MoxfieldType = "collection"
    ):
        self.discord_id: str = discord_id
        self.moxfield_id: str = moxfield_id
        self.moxfield_type: MoxfieldType = moxfield_type

    
    async def get_moxfield_session_id(self, session: AsyncSession, card_name: str) -> str:

        params = {
            "pageSize": 1,
            "q": card_name
        }

        response = await call_moxfield_api(session=session, moxfield_id=self.moxfield_id, moxfield_type=self.moxfield_type, params=params)

        session_id = response.get("searchSessionId", None)

        if not session_id:
            raise Exception(f"Failed to get search session ID for {self.moxfield_id} and card {card_name}")

        return session_id

    async def search_moxfield(self, session: AsyncSession, card_name: str) -> dict[str, CardEntry]:

        session_id = await self.get_moxfield_session_id(session, card_name)

        params = {
            "pageSize": 1000,
            "q": card_name,
            "searchSessionId": session_id
        }

        response = await call_moxfield_api(session=session, moxfield_id=self.moxfield_id, moxfield_type=self.moxfield_type, params=params)

        # Filter all_data
        grouped_items: dict[str, CardEntry] = {}

        for entry in response['data']:
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


