import unittest
from unittest.mock import MagicMock

from main import extract_moxfield_id, filter_trades, parse_search_input
from main import parse_search_list_input

class TestSearchFunction(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.example_available_trades = {
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

        self.second_user_trades = {
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

        self.full_available_trades = {
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
        message = '!search {{ +2 mace }}'
        card_name, collection_number = parse_search_input(message)
        self.assertEqual(card_name, '+2 mace')
        self.assertIsNone(collection_number)

        message = '!search {{ Borrowing 100,000 arrows | 045 }}'
        card_name, collection_number = parse_search_input(message)
        self.assertEqual(card_name, 'Borrowing 100,000 arrows')
        self.assertEqual(collection_number, '45')

    def test_parse_search_list_input_complex(self):
        message = '!search_list {{ +2 mace | _____ Goblin | _____ | TL;DR }}'
        result = parse_search_list_input(message)
        expected = ['+2 mace', '_____ Goblin', '_____', 'TL;DR']
        self.assertEqual(result, expected)

    def test_extract_moxfield_id(self):
        messages = [
            '!link_moxfield https://www.moxfield.com/collection/Tn1Ta-3HsEKtpGYrJG_d6Q/',
            '!link_moxfield https://www.moxfield.com/collection/Tn1Ta-3HsEKtpGYrJG_d6Q',
            '!link_moxfield moxfield.com/collection/Tn1Ta-3HsEKtpGYrJG_d6Q',
            '!link_moxfield Tn1Ta-3HsEKtpGYrJG_d6Q',
            '!link_moxfield abcd1234',
        ]
        
        # Create mock context objects with message.content
        ctxs = []
        for message in messages:
            ctx = MagicMock()
            ctx.message.content = message
            ctxs.append(ctx)

        for (i, ctx) in enumerate(ctxs[:-1]):
            assert extract_moxfield_id(ctxs[i]) == 'Tn1Ta-3HsEKtpGYrJG_d6Q', f"Failed on message: {ctxs[i].message.content}"
        moxfield_id = extract_moxfield_id(ctxs[-1])
        assert not moxfield_id


if __name__ == '__main__':
    unittest.main()
