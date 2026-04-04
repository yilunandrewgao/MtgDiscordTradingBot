from mtg_discord_trading_bot.trader import Trader

def test_group_cards_by_id():
    trader = Trader("123", "abc", "collection")
    
    # Mock Moxfield response data
    mock_response = {
        'data': [
            {
                'id': 'card1',
                'quantity': 2,
                'card': {
                    'name': 'Lightning Bolt',
                    'set_name': 'Alpha',
                    'scryfall_id': '123',
                    'cn': '1'
                }
            },
            {
                'id': 'card2',
                'quantity': 1,
                'card': {
                    'name': 'Black Lotus',
                    'set_name': 'Alpha',
                    'scryfall_id': '456',
                    'cn': '2'
                }
            },
            {
                'id': 'card1',
                'quantity': 3,
                'card': {
                    'name': 'Lightning Bolt',
                    'set_name': 'Alpha',
                    'scryfall_id': '123',
                    'cn': '1'
                }
            }
        ]
    }
    
    result = trader.group_cards_by_id(mock_response)
    
    # Check that card1 has combined quantity
    assert 'card1' in result
    assert result['card1']['count'] == 5  # 2 + 3
    assert result['card1']['name'] == 'Lightning Bolt'

    # Check card2
    assert 'card2' in result
    assert result['card2']['count'] == 1
    assert result['card2']['name'] == 'Black Lotus'
    
    # Check total unique cards
    assert len(result) == 2
