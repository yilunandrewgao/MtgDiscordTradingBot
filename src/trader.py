import logging
from moxfield_api import call_moxfield_collection_api


handler = logging.FileHandler(filename='app.log', encoding='utf-8', mode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

class Trader:
    
    def __init__(
        self,
        discord_id,
        moxfield_id
    ):
        self.discord_id = discord_id
        self.moxfield_id = moxfield_id

    
    def get_moxfield_session_id(self, card_name):
        
        params = {
            "pageSize": 1,
            "q": card_name
        }

        response = call_moxfield_collection_api(moxfield_id=self.moxfield_id, params=params)

        session_id = response.get("searchSessionId", None)

        if not session_id:
            raise Exception(f"Failed to get search session ID for {self.moxfield_id} and card {card_name}")

        return session_id

    def search_moxfield(self, card_name):

        session_id = self.get_moxfield_session_id(card_name)
        
        params = {
            "pageSize": 1000,
            "q": card_name,
            "searchSessionId": session_id
        }

        response = call_moxfield_collection_api(moxfield_id=self.moxfield_id, params=params)

        # Filter all_data
        grouped_items = {}

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


