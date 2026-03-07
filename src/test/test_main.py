import asyncio
import pytest
import unittest
from unittest.mock import MagicMock

from main import extract_moxfield_info, filter_trades, generate_messages_from_lines, parse_search_input, parse_search_list_input
from trader import AvailableTrades, CardEntry

class TestSearchFunction(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.example_available_trades: dict[str, CardEntry] = {
            'yjpW2O1': {
                'count': 4,
                'name': 'Ponder',
                'expansion': 'Tarkir: Dragonstorm Commander',
                'scryfall_id': 'dc69f960-68ba-4315-8146-6a7a82047503',
                'cn': '159'
            },
            'aQJlzZ9': {
                'count': 1,
                'name': 'Ponder',
                'expansion': 'Duskmourn: House of Horror Commander',
                'scryfall_id': '8cbab1d1-25cb-456f-8d1c-3d64eb7265ea',
                'cn': '73'
            },
            'WalWzdG': {
                'count': 1,
                'name': 'Ponder',
                'expansion': 'Lorwyn',
                'scryfall_id': 'ba6b6fc5-5077-4812-b8e9-906783dbaf67',
                'cn': '79'
            }
        }

        self.second_user_trades: dict[str, CardEntry] = {
            'bRnjVOg': {
                'count': 1,
                'name': 'Ponder',
                'expansion': 'Secret Lair Promo',
                'scryfall_id': 'cd165fe9-7de3-4883-a258-e397472db606',
                'cn': '19'
            },
            'xRK4yrn': {
                'count': 2,
                'name': 'Ponder',
                'expansion': 'New Capenna Commander',
                'scryfall_id': '44dcfc0c-b23d-48be-bf3a-a6fc6806c5e1',
                'cn': '229'
            },
            'xRK41BQ': {
                'count': 1,
                'name': 'Ponder',
                'expansion': 'Commander 2018',
                'scryfall_id': '91382955-bcfc-4fb6-8cce-dc107e5b4c32',
                'cn': '96'
            }
        }

        self.full_available_trades: AvailableTrades = {
            'user1': self.example_available_trades,
            '103193318623563776': self.second_user_trades
        }

    def test_search_by_collection_number_159(self):
        """Test filtering trades by collection number 159"""
        cn = '159'

        filtered_trades = filter_trades(self.full_available_trades, cn)

        # Should only contain user1 with the Tarkir: Dragonstorm Commander version
        expected = {
            'user1': {
                'yjpW2O1': {
                    'count': 4,
                    'name': 'Ponder',
                    'expansion': 'Tarkir: Dragonstorm Commander',
                    'scryfall_id': 'dc69f960-68ba-4315-8146-6a7a82047503',
                    'cn': '159'
                }
            }
        }

        self.assertEqual(filtered_trades, expected)

    def test_search_by_collection_number_73(self):
        """Test filtering trades by collection number 73"""
        cn = '73'

        filtered_trades = filter_trades(self.full_available_trades, cn)

        # Should only contain user1 with the Duskmourn version
        expected = {
            'user1': {
                'aQJlzZ9': {
                    'count': 1,
                    'name': 'Ponder',
                    'expansion': 'Duskmourn: House of Horror Commander',
                    'scryfall_id': '8cbab1d1-25cb-456f-8d1c-3d64eb7265ea',
                    'cn': '73'
                }
            }
        }

        self.assertEqual(filtered_trades, expected)

    def test_search_by_collection_number_19(self):
        """Test filtering trades by collection number 19"""
        cn = '19'

        filtered_trades = filter_trades(self.full_available_trades, cn)

        # Should only contain the second user with the Secret Lair Promo version
        expected = {
            '103193318623563776': {
                'bRnjVOg': {
                    'count': 1,
                    'name': 'Ponder',
                    'expansion': 'Secret Lair Promo',
                    'scryfall_id': 'cd165fe9-7de3-4883-a258-e397472db606',
                    'cn': '19'
                }
            }
        }

        self.assertEqual(filtered_trades, expected)

    def test_search_by_nonexistent_collection_number(self):
        """Test filtering by a collection number that doesn't exist"""
        cn = '999'

        filtered_trades = filter_trades(self.full_available_trades, cn)

        # Should be empty
        self.assertEqual(filtered_trades, {})

    def test_parse_search(self):
        card_name, collection_number = parse_search_input('{{ +2 mace }}')
        self.assertEqual(card_name, '+2 mace')
        self.assertIsNone(collection_number)

        card_name, collection_number = parse_search_input('{{ Borrowing 100,000 arrows | 045 }}')
        self.assertEqual(card_name, 'Borrowing 100,000 arrows')
        self.assertEqual(collection_number, '45')

    def test_parse_search_moxfield_format(self):
        card_name, collection_number = parse_search_input('1 Counterspell (CMR) 632')
        self.assertEqual(card_name, 'Counterspell')
        self.assertEqual(collection_number, '632')

    def test_parse_search_moxfield_format_no_set(self):
        card_name, collection_number = parse_search_input('1 Sol Ring')
        self.assertEqual(card_name, 'Sol Ring')
        self.assertIsNone(collection_number)

    def test_parse_search_moxfield_leading_zeros_stripped(self):
        card_name, collection_number = parse_search_input('1 Ponder (M11) 076')
        self.assertEqual(card_name, 'Ponder')
        self.assertEqual(collection_number, '76')

    def test_parse_search_moxfield_multi_card_raises(self):
        with self.assertRaises(ValueError) as ctx:
            parse_search_input('1 Sol Ring\n2 Lightning Bolt (M11) 149')
        self.assertIn('!search_list', str(ctx.exception))

    def test_parse_search_no_args_raises(self):
        with self.assertRaises(ValueError):
            parse_search_input('')

    def test_parse_search_list_input_complex(self):
        result = parse_search_list_input('{{ +2 mace | _____ Goblin | _____ | TL;DR }}')
        self.assertEqual(result, ['+2 mace', '_____ Goblin', '_____', 'TL;DR'])

    def test_parse_search_list_moxfield_format(self):
        content = '1 Sol Ring\n2 Lightning Bolt (M11) 149\n1 Counterspell (CMR) 632'
        self.assertEqual(parse_search_list_input(content), ['Sol Ring', 'Lightning Bolt', 'Counterspell'])

    def test_parse_search_list_no_args_raises(self):
        with self.assertRaises(ValueError):
            parse_search_list_input('')


@pytest.mark.parametrize("message", [
    '!link_moxfield https://www.moxfield.com/collection/Tn1Ta-3HsEKtpGYrJG_d6Q/',
    '!link_moxfield https://www.moxfield.com/collection/Tn1Ta-3HsEKtpGYrJG_d6Q',
    '!link_moxfield moxfield.com/collection/Tn1Ta-3HsEKtpGYrJG_d6Q',
    '!link_moxfield Tn1Ta-3HsEKtpGYrJG_d6Q',
])
def test_extract_moxfield_info_collection(message):
    ctx = MagicMock()
    ctx.message.content = message
    result = asyncio.run(extract_moxfield_info(ctx))
    assert result == ('Tn1Ta-3HsEKtpGYrJG_d6Q', 'collection')


def test_extract_moxfield_info_collection_invalid():
    ctx = MagicMock()
    ctx.message.content = '!link_moxfield abcd1234'
    result = asyncio.run(extract_moxfield_info(ctx))
    assert not result


@pytest.mark.parametrize("message", [
    '!link_moxfield https://moxfield.com/binders/6fs4Mh8xUEScfzKmh0av6Q',
    '!link_moxfield https://moxfield.com/binders/6fs4Mh8xUEScfzKmh0av6Q/',
    '!link_moxfield moxfield.com/binders/6fs4Mh8xUEScfzKmh0av6Q',
])
def test_extract_moxfield_info_binder(message):
    ctx = MagicMock()
    ctx.message.content = message
    result = asyncio.run(extract_moxfield_info(ctx))
    assert result == ('6fs4Mh8xUEScfzKmh0av6Q', 'binder')

@pytest.mark.parametrize(
    ('lines', 'messages'),
    [
        (
            [
                'alice has available trades\n',
                '4 copies of arcane denial\n',
                '4 copies of absorb\n',
                '4 copies of annul\n',
            ],
            [
                'alice has available trades\n',
                '4 copies of arcane denial\n4 copies of absorb\n',
                '4 copies of annul\n'
            ]
        ),
        (
            [], []
        ),
        (
            [
                'carol has available trades\n',
                '4 copies of censor\n'
            ],
            [
                'carol has available trades\n4 copies of censor\n'
            ]
        ),
    ]
)
def test_generate_messages_from_lines(lines, messages):

    assert generate_messages_from_lines(lines, max_message_length=50) == messages

if __name__ == '__main__':
    unittest.main()
