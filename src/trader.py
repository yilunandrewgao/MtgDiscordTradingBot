import requests
import logging


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

        
    def search_echomtg_collection(self, card_name):

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
        
    def search_moxfield_api(self, card_name):
        