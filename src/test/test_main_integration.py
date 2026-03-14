from unittest.mock import MagicMock

import pytest

from main import extract_moxfield_info
from models.moxfield_types import MoxfieldAsset


@pytest.mark.parametrize("message", [
    '!link_moxfield https://www.moxfield.com/collection/Tn1Ta-3HsEKtpGYrJG_d6Q/',
    '!link_moxfield https://www.moxfield.com/collection/Tn1Ta-3HsEKtpGYrJG_d6Q',
    '!link_moxfield moxfield.com/collection/Tn1Ta-3HsEKtpGYrJG_d6Q',
])
def test_extract_moxfield_info_collection(message):
    ctx = MagicMock()
    ctx.message.content = message
    assert extract_moxfield_info(ctx, MoxfieldAsset.COLLECTION) == ('Tn1Ta-3HsEKtpGYrJG_d6Q', MoxfieldAsset.COLLECTION)


@pytest.mark.parametrize("message", [
    '!link_moxfield abcd1234',
    '!link_moxfield Tn1Ta-3HsEKtpGYrJG_d6Q',
])
def test_extract_moxfield_info_collection_invalid(message):
    ctx = MagicMock()
    ctx.message.content = message
    with pytest.raises(ValueError):
        extract_moxfield_info(ctx)


@pytest.mark.parametrize("message", [
    '!link_moxfield https://moxfield.com/binders/6fs4Mh8xUEScfzKmh0av6Q',
    '!link_moxfield https://moxfield.com/binders/6fs4Mh8xUEScfzKmh0av6Q/',
    '!link_moxfield moxfield.com/binders/6fs4Mh8xUEScfzKmh0av6Q',
])
def test_extract_moxfield_info_binder(message):
    ctx = MagicMock()
    ctx.message.content = message
    assert extract_moxfield_info(ctx, MoxfieldAsset.BINDER) == ('6fs4Mh8xUEScfzKmh0av6Q', MoxfieldAsset.BINDER)

@pytest.mark.parametrize("message", [
    '!link_moxfield https://moxfield.com/decks/ugc1TPPrMkWgfndRILegww',
    '!link_moxfield moxfield.com/decks/ugc1TPPrMkWgfndRILegww',
])
def test_extract_moxfield_info_deck(message):
    ctx = MagicMock()
    ctx.message.content = message
    assert extract_moxfield_info(ctx, MoxfieldAsset.DECK) == ('ugc1TPPrMkWgfndRILegww', MoxfieldAsset.DECK)
