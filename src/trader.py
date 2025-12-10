import requests
import logging
import json
import os

from moxfield.fetch_collections import fetch_collection


handler = logging.FileHandler(filename='app.log', encoding='utf-8', mode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

class Trader:
    
    def __init__(
        self,
        discord_id,
        echomtg_token,
        moxfield_id
    ):
        self.discord_id = discord_id
        self.echomtg_token = echomtg_token
        self.moxfield_id = moxfield_id
        
    def search_echomtg(self, card_name):

        # Call the Echo MTG API
        url = f"https://api.echomtg.com/api/inventory/search?name={card_name}"
        headers = {
            "Authorization": f"Bearer {self.echomtg_token}"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            if not response.text:
                logging.debug(f"Failed to call echomtg using auth token for discord_id: {self.discord_id}")
                return {}
            
            data = response.json()
            
            # Group items by multiverseID
            grouped_items = {}
            
            if data.get("status") == "success" and "results" in data:
                for item in data["results"]:
                    multiverse_id = item.get("multiverseID")
                    
                    if multiverse_id:
                        if multiverse_id not in grouped_items:
                            grouped_items[multiverse_id] = {
                                "count": 0,
                                "name": item.get("name"),
                                "expansion": item.get("expansion"),
                                "image": item.get("image")
                            }
                        grouped_items[multiverse_id]["count"] += 1
            
            return grouped_items
            
        except requests.exceptions.RequestException as e:
            print(f"Error calling Echo MTG API: {e}")
            return {}
        
    def loose_match(self, strict_card_name, query):

        return query.lower().strip() in strict_card_name.lower().strip()
        
        
    def search_moxfield(self, card_name):

        file_path = f"src/moxfield/collections/{self.moxfield_id}.json"

        if not os.path.exists(file_path):
            logging.debug(f"Collection file not found: {file_path}. Fetching now...")
            fetch_collection(self.moxfield_id)

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            grouped_items = {}

            for entry in data.get("data", []):
                card = entry.get("card", {})
                if self.loose_match(card.get("name"), card_name):
                    id = entry.get("id")
                    quantity = entry.get("quantity", 1)

                    if id not in grouped_items:
                        grouped_items[id] = {
                            "count": quantity,
                            "name": card.get("name"),
                            "expansion": card.get("set_name"),
                            "scryfall_id": card.get("scryfall_id")
                        }
                    else:
                        grouped_items[id]["count"] += quantity

            return grouped_items

        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error reading collection file: {e}")
            return {}
