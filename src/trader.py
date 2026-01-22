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
    

    def search_moxfield(self, card_name):
        url = f"https://api2.moxfield.com/v1/collections/search/{self.moxfield_id}"

        params = {
            "pageSize": 1000,
            "q": card_name
        }

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
                response = {}
            else:
                response = response.json()

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

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch collection {self.moxfield_id}: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response for {self.moxfield_id}: {e}")
