import requests
import logging
import json

from curl_cffi import requests as curl_requests

def call_moxfield_api(url, params=None):

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
            logging.debug(f"Failed to call moxfield using collection")
            return {}
        else:
            return response.json()

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch collection: {e}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON response: {e}")

def call_moxfield_collection_api(moxfield_id, params=None):

    url = f"https://api2.moxfield.com/v1/collections/search/{moxfield_id}"
    return call_moxfield_api(url, params=params)

def call_moxfield_deck_api(deck_id, params=None):

    url = f"https://api2.moxfield.com/v3/decks/all/{deck_id}"
    return call_moxfield_api(url, params=params)