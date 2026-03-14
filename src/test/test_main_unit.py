import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import unittest

from main import generate_messages_from_lines, parse_search_input
from main import link_moxfield, search, search_exact
from decklist_parser import CardQuery, Printing
from models.moxfield_types import MoxfieldAsset

class TestSearchFunction(unittest.TestCase):

    def test_parse_search_single_card(self):
        self.assertEqual(parse_search_input('1 Counterspell (CMR) 632'),
                         [CardQuery('Counterspell', set_code='CMR', collector_number='632')])

    def test_parse_search_multiple_cards(self):
        content = '1 Sol Ring\n2 Lightning Bolt (M11) 149\n1 Counterspell (CMR) 632'
        self.assertEqual(parse_search_input(content), [
            CardQuery('Sol Ring'),
            CardQuery('Lightning Bolt', set_code='M11', collector_number='149'),
            CardQuery('Counterspell', set_code='CMR', collector_number='632'),
        ])

    def test_parse_search_no_args_raises(self):
        with self.assertRaises(ValueError):
            parse_search_input('')

    def test_to_moxfield_query_name_only(self):
        self.assertEqual(CardQuery('Sol Ring').to_moxfield_query(), '(Sol Ring)')

    def test_to_moxfield_query_with_set_and_number(self):
        self.assertEqual(CardQuery('Counterspell', set_code='CMR', collector_number='632').to_moxfield_query(), '(Counterspell set:CMR number:632)')

    def test_to_moxfield_query_set_only(self):
        self.assertEqual(CardQuery('Ponder', set_code='M11').to_moxfield_query(), '(Ponder set:M11)')


class TestSearchCommand(unittest.TestCase):

    def _run_command(self, command, content: str) -> AsyncMock:
        ctx = MagicMock()
        ctx.author.id = 999
        ctx.guild.members = []
        ctx.send = AsyncMock()
        mock_tm = MagicMock()
        mock_tm.search_for_card = AsyncMock(return_value={})
        with patch('main.trade_manager', mock_tm):
            asyncio.run(command(ctx, content=content))
        return mock_tm.search_for_card

    def test_search_ignores_set_and_number(self):
        """!search should query by name only, ignoring set and collector number."""
        search_for_card = self._run_command(search, '1 Ponder (LRW) 79')
        self.assertEqual(search_for_card.call_args.args[0], '"Ponder"')

    def test_search_multiple_cards(self):
        """!search with multiple cards should join names with or."""
        search_for_card = self._run_command(search, '1 Ponder\n1 Counterspell (CMR) 632')
        self.assertEqual(search_for_card.call_args.args[0], '"Ponder" or "Counterspell"')

    def test_search_exact_passes_full_query_and_finish(self):
        """!search_exact should pass the full moxfield query and nonFoil finish for normal cards."""
        search_for_card = self._run_command(search_exact, '1 Ponder (LRW) 79')
        self.assertEqual(search_for_card.call_args.args[0], '(Ponder set:LRW number:79)')
        self.assertEqual(search_for_card.call_args.kwargs['finish'], 'nonFoil')

    def test_search_exact_foil(self):
        """!search_exact with *F* should use foil finish."""
        search_for_card = self._run_command(search_exact, '1 Ponder (LRW) 79 *F*')
        self.assertEqual(search_for_card.call_args.kwargs['finish'], 'foil')

    def test_search_exact_etched(self):
        """!search_exact with *E* should use etched finish."""
        search_for_card = self._run_command(search_exact, '1 Sol Ring (SLC) 27 *E*')
        self.assertEqual(search_for_card.call_args.kwargs['finish'], 'etched')

    def test_search_exact_partitions_by_finish(self):
        """!search_exact with mixed finishes should make one call per finish type."""
        search_for_card = self._run_command(search_exact, '1 Ponder (LRW) 79\n1 Counterspell (CMR) 632 *F*')
        self.assertEqual(search_for_card.call_count, 2)
        finishes = {call.kwargs['finish'] for call in search_for_card.call_args_list}
        self.assertEqual(finishes, {'nonFoil', 'foil'})


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


@pytest.mark.parametrize(
    ('message_content', 'expected_moxfield_type'),
    [
        ('!link_moxfield https://www.moxfield.com/collection/Tn1Ta-3HsEKtpGYrJG_d6Q/', MoxfieldAsset.COLLECTION),
        ('!link_moxfield https://www.moxfield.com/binders/6fs4Mh8xUEScfzKmh0av6Q', MoxfieldAsset.BINDER),
    ]
)
def test_link_moxfield_calls_extract_moxfield_info_with_correct_args(message_content, expected_moxfield_type):
    """Test that _link_moxfield calls extract_moxfield_info with the correct moxfield type based on URL"""
    ctx = MagicMock()
    ctx.message.content = message_content

    with patch('main._link_moxfield') as mock_internal_link_moxfield:
        asyncio.run(link_moxfield(ctx))
        mock_internal_link_moxfield.assert_called_once_with(ctx, expected_moxfield_type)


if __name__ == '__main__':
    unittest.main()
