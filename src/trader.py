import requests
import logging
import json
import os

from curl_cffi import requests as curl_requests


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

    def call_moxfield_api(self, params=None):

        url = f"https://api2.moxfield.com/v1/collections/search/{self.moxfield_id}"

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
            response.raise_for_status()  # Raises an HTTPError for bad responses

            if not response.text:
                logging.debug(f"Failed to call moxfield using collection id: {self.moxfield_id}")
                return {}
            else:
                return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch collection {self.moxfield_id}: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response for {self.moxfield_id}: {e}")
        
    def get_moxfield_session_id(self, card_name):
        
        params = {
            "pageSize": 1,
            "q": card_name
        }

        response = self.call_moxfield_api(params=params)

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

        response = self.call_moxfield_api(params=params)

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


