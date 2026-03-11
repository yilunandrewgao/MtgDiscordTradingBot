import json
import os
import tempfile
import unittest
from unittest.mock import patch

from trade_manager import TradeManager


def test_search_for_card_integration():
    pass


class TestWishlistPersistence(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump({"users": [
            {
                "discord_id": "123",
                "moxfield_id": "abc",
                "moxfield_type": "collection",
            }
        ]}, self.tmp)
        self.tmp.close()
        self.users_file = self.tmp.name

    def tearDown(self):
        os.unlink(self.users_file)

    def test_set_wishlist_persists(self):
        with patch('trade_manager.USERS_FILE', self.users_file):
            tm = TradeManager()
            tm.set_wishlist("123", "deck_xyz")

        with open(self.users_file) as f:
            data = json.load(f)
        user = next(u for u in data["users"] if u["discord_id"] == "123")
        self.assertEqual(user["wishlist_id"], "deck_xyz")

    def test_load_wishlist_id_from_json(self):
        with open(self.users_file, 'w') as f:
            json.dump({"users": [
                {
                    "discord_id": "123",
                    "moxfield_id": "abc",
                    "moxfield_type": "collection",
                    "wishlist_id": "deck_xyz",
                }
            ]}, f)

        with patch('trade_manager.USERS_FILE', self.users_file):
            tm = TradeManager()

        self.assertEqual(tm.traders["123"].wishlist_id, "deck_xyz")
        self.assertEqual(tm.traders["123"].wishlist_url, "https://moxfield.com/decks/deck_xyz")

    def test_remove_wishlist_clears_key(self):
        with open(self.users_file, 'w') as f:
            json.dump({"users": [
                {
                    "discord_id": "123",
                    "moxfield_id": "abc",
                    "moxfield_type": "collection",
                    "wishlist_id": "deck_xyz",
                }
            ]}, f)

        with patch('trade_manager.USERS_FILE', self.users_file):
            tm = TradeManager()
            removed = tm.remove_wishlist("123")

        self.assertTrue(removed)
        with open(self.users_file) as f:
            data = json.load(f)
        user = next(u for u in data["users"] if u["discord_id"] == "123")
        self.assertNotIn("wishlist_id", user)

    def test_remove_wishlist_returns_false_when_no_wishlist(self):
        with patch('trade_manager.USERS_FILE', self.users_file):
            tm = TradeManager()
            result = tm.remove_wishlist("123")
        self.assertFalse(result)

    def test_remove_wishlist_returns_false_for_unknown_trader(self):
        with patch('trade_manager.USERS_FILE', self.users_file):
            tm = TradeManager()
            result = tm.remove_wishlist("999")
        self.assertFalse(result)

    def test_missing_wishlist_id_defaults_to_none(self):
        with patch('trade_manager.USERS_FILE', self.users_file):
            tm = TradeManager()
        self.assertIsNone(tm.traders["123"].wishlist_id)
        self.assertIsNone(tm.traders["123"].wishlist_url)

    def test_set_wishlist_omits_key_when_none(self):
        with patch('trade_manager.USERS_FILE', self.users_file):
            tm = TradeManager()
            tm.set_wishlist("123", None)

        with open(self.users_file) as f:
            data = json.load(f)
        user = next(u for u in data["users"] if u["discord_id"] == "123")
        self.assertNotIn("wishlist_id", user)


if __name__ == '__main__':
    unittest.main()
