from curl_cffi import requests
import json
import os
import logging

from config import USERS_FILE

logger = logging.getLogger(__name__)
handler = logging.FileHandler(filename='app.log', encoding='utf-8', mode='w')
logger.addHandler(handler)

def fetch_paginated_collection(moxfield_id, page = 1):
    """
    Fetch collection data from Moxfield API and save to JSON file.

    Args:
        moxfield_id (str): The Moxfield collection ID

    Raises:
        Exception: If the API request fails or returns non-200 status
    """
    url = f"https://api2.moxfield.com/v1/collections/search/{moxfield_id}"

    params = {
        "pageNumber": page,
        "pageSize": 1000
    }

    try:
        response = requests.get(
            url, 
            headers={
                "User-Agent": "MtgDiscordTrading",
                "Host": "api2.moxfield.com",
            },
            params = params,
            impersonate="chrome"
        )
        response.raise_for_status()  # Raises an HTTPError for bad responses

        if not response.text:
            logging.debug(f"Failed to call moxfield using collection id: {moxfield_id}")
            data = {}
        else:
            data = response.json()

        return data

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch collection {moxfield_id}: {e}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON response for {moxfield_id}: {e}")
    
def fetch_collection(moxfield_id):
    """
    Fetch complete collection data from Moxfield API and save to JSON file.

    Args:
        moxfield_id (str): The Moxfield collection ID

    Raises:
        Exception: If the API request fails or returns non-200 status
    """
    # Fetch the first page to get totalPages and initial data
    first_page = fetch_paginated_collection(moxfield_id, page=1)
    if not first_page:
        logging.warning(f"No data returned for collection {moxfield_id}")
        return

    total_pages = first_page.get('totalPages', 1)
    all_data = first_page.get('data', [])

    # Fetch remaining pages
    for page in range(2, total_pages + 1):
        page_data = fetch_paginated_collection(moxfield_id, page=page)
        if page_data and 'data' in page_data:
            all_data.extend(page_data['data'])

    # Prepare the full collection data
    full_collection = first_page.copy()
    full_collection['data'] = all_data

    # Save to JSON file
    os.makedirs("src/moxfield/collections", exist_ok=True)
    file_path = f"src/moxfield/collections/{moxfield_id}.json"
    with open(file_path, 'w') as f:
        json.dump(full_collection, f, indent=2)

    logging.info(f"Saved collection {moxfield_id} with {len(all_data)} cards to {file_path}")

def fetch_all_collections():
    """
    Fetch collections for all users in users.json that have moxfield_id.
    """
    with open(f"src/{USERS_FILE}", 'r') as f:
        users_data = json.load(f)

    for user in users_data.get("users", []):
        if "moxfield_id" in user and user["moxfield_id"]:
            try:
                fetch_collection(user["moxfield_id"])
            except Exception as e:
                logging.error(f"Failed to fetch collection for user {user.get('discord_id', 'unknown')}: {e}")

if __name__ == '__main__':
    fetch_all_collections()
