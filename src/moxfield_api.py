import logging
import json

from curl_cffi import requests as curl_requests
from typing import Any
from curl_cffi.requests import AsyncSession, RequestsError
from models.moxfield_types import MoxfieldAsset

def get_moxfield_url(moxfield_id: str, moxfield_type: MoxfieldAsset) -> str:
    match moxfield_type:
        case MoxfieldAsset.BINDER:
            return f'https://api2.moxfield.com/v1/trade-binders/{moxfield_id}/search'
        case MoxfieldAsset.DECK:
            return f'https://api2.moxfield.com/v2/decks/all/{moxfield_id}'
        case MoxfieldAsset.COLLECTION:
            return f'https://api2.moxfield.com/v1/collections/search/{moxfield_id}'

def call_moxfield_api_sync(
    moxfield_id: str,
    moxfield_type: MoxfieldAsset = MoxfieldAsset.COLLECTION,
    params: dict[str, str | int] | None = None
) -> dict[str, Any]:

    try:
        response = curl_requests.get(
            get_moxfield_url(moxfield_id, moxfield_type),
            headers={
                'User-Agent': 'MtgDiscordTrading',
                'Host': 'api2.moxfield.com',
            },
            params=params,
            impersonate='chrome'
        )
        response.raise_for_status()
        if not response.text:
            logging.debug(f'Failed to call moxfield using collection id: {moxfield_id}')
            return {}
        return response.json()

    except RequestsError as e:
        raise Exception(f'Failed to fetch collection {moxfield_id}: {e}')
    except json.JSONDecodeError as e:
        raise Exception(f'Failed to parse JSON response for {moxfield_id}: {e}')

async def call_moxfield_api(
    session: AsyncSession,
    moxfield_id: str,
    moxfield_type: MoxfieldAsset = MoxfieldAsset.COLLECTION,
    params: dict[str, str | int] | None = None
) -> dict[str, Any]:

    try:
        response = await session.get(get_moxfield_url(moxfield_id, moxfield_type), params=params)
        response.raise_for_status()
        if not response.text:
            logging.debug(f'Failed to call moxfield using collection id: {moxfield_id}')
            return {}
        return response.json()

    except RequestsError as e:
        raise Exception(f'Failed to fetch collection {moxfield_id}: {e}')
    except json.JSONDecodeError as e:
        raise Exception(f'Failed to parse JSON response for {moxfield_id}: {e}')
    
def get_deck_export_id(deck_id: str) -> str:
    response = call_moxfield_api_sync(moxfield_id=deck_id, moxfield_type=MoxfieldAsset.DECK)
    if 'exportId' not in response:
        raise Exception(f"Failed to get export ID for deck {deck_id}")
    return response['exportId']

def get_decklist_export(deck_id: str) -> str:
    export_id = get_deck_export_id(deck_id)

    params = {
        'arenaOnly': False,
        'format': 'full',
        'includeFinish': True,
        'exportId': export_id,
        'pricingProvider': 'tcgplayer',
        'ignoreFlavorNames': False
    }

    export_url = get_moxfield_url(deck_id, MoxfieldAsset.DECK) + '/export'
    response = curl_requests.get(
        export_url,
        headers={
            'User-Agent': 'MtgDiscordTrading',
            'Host': 'api2.moxfield.com',
        },
        params=params,
        impersonate='chrome'
    )
    response.raise_for_status()
    return response.text
